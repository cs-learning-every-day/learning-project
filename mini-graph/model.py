from peewee import *


database = MySQLDatabase(
    "classicmodels",
    **{
        "charset": "utf8",
        "sql_mode": "PIPES_AS_CONCAT",
        "use_unicode": True,
        "host": "",
        "port": 15306,
        "user": "root",
        "password": "",
    },
)


def field_names(fields):
    return [f.name if isinstance(f, Field) else f.strip() for f in fields]


def getattrs(obj, names):
    return {name: obj.get(name) for name in names if name in obj}


class UnknownField(object):
    def __init__(self, *_, **__):
        pass


class PermissionedModel(Model):
    default_model_permission = 0o606
    default_field_permission = 0o604
    default_role = 0o006

    def get_role(self, user_id):
        return self.default_role

    @classmethod
    def model_perm(cls):
        return getattr(cls._meta, "permission", cls.default_model_permission)

    @classmethod
    def field_perms(cls):
        return {f: cls.field_perm(f) for f in cls._meta.sorted_fields}

    @classmethod
    def field_perm(cls, field):
        perm = cls.default_field_permission if field._hidden is False else field._hidden
        return perm & cls.model_perm()

    @classmethod
    def fields(cls, op_perm=0, role=0):
        return [field for field, permission in cls.field_perms().items() if permission & op_perm & role]

    def readable_fields(self, user_id=0):
        return self.fields(0o444, self.get_role(user_id))

    def writable_fields(self, user_id=0):
        return self.fields(0o222, self.get_role(user_id))

    def to_dict(self, user_id=0, only=None):
        print(only)
        readable_fields = [
            field
            for field in field_names(self.readable_fields(user_id))
            if (only is None or not any(only) or field in field_names(only))
        ]
        print(readable_fields)
        return getattrs(self.__data__, readable_fields)

    def from_dict(self, items, user_id=0):
        for key, value in items.items():
            if key in field_names(self.writable_fields(user_id)):
                setattr(self, key, value)
            else:
                raise Exception(f"Failed {key} is not writeable for user")
        return self

    class Meta:
        database = database


class BaseModel(PermissionedModel):
    pass


class Offices(BaseModel):
    address_line1 = CharField(column_name="addressLine1")
    address_line2 = CharField(column_name="addressLine2", null=True)
    city = CharField()
    country = CharField()
    office_code = CharField(column_name="officeCode", primary_key=True)
    phone = CharField()
    postal_code = CharField(column_name="postalCode")
    state = CharField(null=True)
    territory = CharField()

    class Meta:
        table_name = "offices"


class Employees(BaseModel):
    email = CharField(_hidden=0o600)
    employee_number = AutoField(column_name="employeeNumber")
    extension = CharField()
    first_name = CharField(column_name="firstName")
    job_title = CharField(column_name="jobTitle")
    last_name = CharField(column_name="lastName")
    office_code = ForeignKeyField(column_name="officeCode", field="office_code", model=Offices, backref="employees")
    reports_to = ForeignKeyField(column_name="reportsTo", field="employee_number", model="self", null=True)

    class Meta:
        table_name = "employees"

    def get_role(self, user_id):
        return 0o600 if user_id == self.employee_number else 0o004


class Customers(BaseModel):
    address_line1 = CharField(column_name="addressLine1")
    address_line2 = CharField(column_name="addressLine2", null=True)
    city = CharField()
    contact_first_name = CharField(column_name="contactFirstName")
    contact_last_name = CharField(column_name="contactLastName")
    country = CharField()
    credit_limit = DecimalField(column_name="creditLimit", null=True)
    customer_name = CharField(column_name="customerName")
    customer_number = AutoField(column_name="customerNumber")
    phone = CharField()
    postal_code = CharField(column_name="postalCode", null=True)
    sales_rep_employee_number = ForeignKeyField(
        column_name="salesRepEmployeeNumber", field="employee_number", model=Employees, null=True
    )
    state = CharField(null=True)

    class Meta:
        table_name = "customers"


class Orders(BaseModel):
    comments = TextField(null=True)
    customer_number = ForeignKeyField(column_name="customerNumber", field="customer_number", model=Customers)
    order_date = DateField(column_name="orderDate")
    order_number = AutoField(column_name="orderNumber")
    required_date = DateField(column_name="requiredDate")
    shipped_date = DateField(column_name="shippedDate", null=True)
    status = CharField()

    class Meta:
        table_name = "orders"
        permission = 0o600


class Productlines(BaseModel):
    html_description = TextField(column_name="htmlDescription", null=True)
    image = TextField(null=True)
    product_line = CharField(column_name="productLine", primary_key=True)
    text_description = CharField(column_name="textDescription", null=True)

    class Meta:
        table_name = "productlines"


class Products(BaseModel):
    msrp = DecimalField(column_name="MSRP")
    buy_price = DecimalField(column_name="buyPrice")
    product_code = CharField(column_name="productCode", primary_key=True)
    product_description = TextField(column_name="productDescription")
    product_line = ForeignKeyField(column_name="productLine", field="product_line", model=Productlines)
    product_name = CharField(column_name="productName")
    product_scale = CharField(column_name="productScale")
    product_vendor = CharField(column_name="productVendor")
    quantity_in_stock = IntegerField(column_name="quantityInStock")

    class Meta:
        table_name = "products"


class Orderdetails(BaseModel):
    order_line_number = IntegerField(column_name="orderLineNumber")
    order_number = ForeignKeyField(column_name="orderNumber", field="order_number", model=Orders)
    price_each = DecimalField(column_name="priceEach")
    product_code = ForeignKeyField(column_name="productCode", field="product_code", model=Products)
    quantity_ordered = IntegerField(column_name="quantityOrdered")

    class Meta:
        table_name = "orderdetails"
        indexes = ((("order_number", "product_code"), True),)
        primary_key = CompositeKey("order_number", "product_code")


class Payments(BaseModel):
    amount = DecimalField()
    check_number = CharField(column_name="checkNumber")
    customer_number = ForeignKeyField(column_name="customerNumber", field="customer_number", model=Customers)
    payment_date = DateField(column_name="paymentDate")

    class Meta:
        table_name = "payments"
        indexes = ((("customer_number", "check_number"), True),)
        primary_key = CompositeKey("check_number", "customer_number")
