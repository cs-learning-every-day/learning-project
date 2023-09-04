"""
 经过讨论，明确了功能要求：
* 对于任何数据，可以通过类型和id获取信息，比如 /employees/1286 或 /offices/3
* 查询某个类型的所有数据，比如 /employees 或 /offices
* 支持关联查询，比如 /offices/3/employees
* 支持分页，比如 /employees?page=1&size=5，并且对于paging和size做保护（限制最大值），防止数据库过慢
* 支持简单用户认证（先不考虑安全，可通过querystring的user_id参数指定）
* 返回JSON要求是好看格式的
* 统一的错误处理
* 支持排序，比如 /employees?sort=-office_code,firstName,lastName (-表示降序,+表示升序)
* 支持filter，比如 /employees?filter=employee_number>1200+and+office_code==3
* 支持fields选择，比如 /employees?fields=firstName,lastName,extension
* Table级别和Field 级别的权限控制，比如orders表的数据，只有自己能看，比如employee表所有人都能看，但其中的email字段只有自己能看。   
"""
import json
import typing
import uvicorn
from fastapi import FastAPI, Depends, Body, Request
from fastapi.responses import JSONResponse
from fastapi.datastructures import QueryParams
from peewee import ModelSelect, Expression, OP
from model import BaseModel
from typing import Annotated

import ast
import operator
from functools import reduce


class IndentJSONResponse(JSONResponse):
    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(",", ":"),
        ).encode("utf-8")


app = FastAPI(default_response_class=IndentJSONResponse)


@app.exception_handler(Exception)
async def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    return IndentJSONResponse(status_code=400, content={"message": f"{base_error_message}. Detail: {err}"})


_resources = {sub._meta.name: sub for sub in BaseModel.__subclasses__()}


def get_resource(kind):
    return _resources[kind]


def get_instance(kind, id):
    return get_resource(kind).get_by_id(id)


Resource = Annotated[type(BaseModel), Depends(get_resource)]
Instance = Annotated[BaseModel, Depends(get_instance)]


def get_oeprator(op: ast):
    return OP.get(op.__class__.__name__.upper())


# http://127.0.0.1:8000/employees?fields=employee_number,last_name&filter=employee_number%3E1200+and+office_code==3
def expr(exp: Expression | str, model: BaseModel):
    match exp:
        case str():
            return expr(ast.parse(exp, mode="eval").body, model)
        case ast.Constant():
            return exp.value
        case ast.Name():
            return getattr(model, exp.id)
        case ast.Tuple() | ast.List():
            return [expr(e, model) for e in exp.elts]
        case ast.UnaryOp():
            return expr(exp.operand, model).desc() if isinstance(exp.op, ast.USub) else expr(exp.operand, model).asc()
        case ast.BoolOp():
            elements = [expr(e, model) for e in exp.values]
            return reduce(operator.and_, elements) if isinstance(exp.op, ast.And) else reduce(operator.or_, elements)
        case ast.Compare():
            return Expression(
                expr(exp.left, model),
                get_oeprator(exp.ops[0]),
                expr(exp.comparators[0], model),
            )
    raise NotImplementedError(f"Expression [{exp}] not supported yet")


def ensure_tuple(data):
    if isinstance(data, (list, tuple)):
        return tuple(data)
    return (data,)


def with_query(select: ModelSelect, func: str, value: str | None):
    if value:
        exp = expr(value, select.model)
        return getattr(select, func)(*ensure_tuple(exp))
    return select


def with_paging(select: ModelSelect, query: QueryParams, user_id: int):
    page = int(query.get("page", 1))
    size = int(query.get("size", 5))

    if page > 100 or size > 100:
        raise ValueError("Page and Size must be less than 100")

    count = select.count()
    select = select.paginate(page, size)

    return {
        "data": [o.to_dict(user_id, only=query.get("fields", "").split(",")) for o in select],
        "pagination": {"count": count, "page": page, "size": size},
    }


def with_psf(select: ModelSelect, query: QueryParams, user_id: int):
    select = with_query(select, "where", query.get("filter"))
    select = with_query(select, "order_by", query.get("sort"))
    select = with_query(select, "select", query.get("fields"))

    return with_paging(select, query, user_id)


@app.get("/{kind}")
def _(res: Resource, req: Request, user_id: int = 0):
    return with_psf(res.select(), req.query_params, user_id)


@app.get("/{kind}/{id}")
def _(ins: Instance, user_id: int = 0):
    return ins.to_dict(user_id)


@app.get("/{kind}/{id}/{edge}")
def _(ins: Instance, edge: str, req: Request, user_id: int = 0):
    return with_psf(getattr(ins, edge), req.query_params, user_id)


@app.post("/{kind}/{id}")
def _(ins: Instance, user_id: int = 0, props: dict = Body()):
    return ins.from_dict(props, user_id).save()


if __name__ == "__main__":
    uvicorn.run(app="graph:app", host="0.0.0.0", reload=True)
