package tcp

import (
	"bufio"
	"context"
	"go-redis/lib/logger"
	"go-redis/lib/sync/atomic"
	"go-redis/lib/sync/wait"
	"io"
	"net"
	"sync"
	"time"
)

type EchoClient struct {
	Conn    net.Conn
	Waiting wait.Wait
}

func (e *EchoClient) Close() error {
	e.Waiting.WaitWithTimeout(10 * time.Second)
	e.Conn.Close()
	return nil
}

type EchoHandler struct {
	activeConn sync.Map
	closing    atomic.Boolean
}

func NewHandler() *EchoHandler {
	return &EchoHandler{}
}

func (e *EchoHandler) Handle(ctx context.Context, conn net.Conn) {
	if e.closing.Get() {
		_ = conn.Close()
	}
	client := &EchoClient{
		Conn: conn,
	}
	e.activeConn.Store(client, struct{}{})
	reader := bufio.NewReader(conn)
	for {
		msg, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				logger.Info("Connection close")
				e.activeConn.Delete(client)
			} else {
				logger.Warn(err)
			}
			return
		}
		client.Waiting.Add(1)
		b := []byte(msg)
		_, _ = conn.Write(b)
		client.Waiting.Done()
	}
}
func (e *EchoHandler) Close() error {
	logger.Info("handler shutting down")
	e.closing.Set(true)
	e.activeConn.Range(func(key, value any) bool {
		client := key.(*EchoClient)
		client.Close()
		return true
	})
	return nil
}
