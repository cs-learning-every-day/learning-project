package database

import "strings"

var cmdTable = make(map[string]*command)

type command struct {
	exector ExecFunc
	arity   int
}

func RegisterCommand(name string, exector ExecFunc, arity int) {
	cmdTable[strings.ToLower(name)] = &command{
		exector: exector,
		arity:   arity,
	}
}
