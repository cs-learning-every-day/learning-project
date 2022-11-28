package cluster

import "go-redis/interface/resp"

func makeRouter() map[string]CmdFunc {
	m := make(map[string]CmdFunc)
	m["exists"] = defaultFunc
	m["type"] = defaultFunc
	m["set"] = defaultFunc
	m["setnx"] = defaultFunc
	m["get"] = defaultFunc
	m["getset"] = defaultFunc
	m["ping"] = ping
	m["rename"] = rename
	m["renamenx"] = rename
	m["flushdb"] = flushdb
	m["del"] = delete
	m["select"] = execSelect
	return m
}

// GET key
// SET k1 v1
func defaultFunc(cluster *ClusterDatabase, c resp.Connection, cmdArgs [][]byte) resp.Reply {
	key := string(cmdArgs[1])
	peer := cluster.peerPicker.PickNode(key)
	return cluster.relay(peer, c, cmdArgs)
}
