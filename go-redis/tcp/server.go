package tcp

import (
    "context"
    "fmt"
    "go-redis/interface/tcp"
    "go-redis/lib/logger"
    "net"
    "os"
    "os/signal"
    "sync"
    "syscall"
)

type Config struct {
    Address string
}

func ListenAndServeWithSignal(cfg *Config, handler tcp.Handler) error {
    closeChan := make(chan struct{})
    sigChan := make(chan os.Signal)

    signal.Notify(sigChan, syscall.SIGHUP, syscall.SIGQUIT, syscall.SIGTERM, syscall.SIGINT)

    go func() {
        sig := <-sigChan
        switch sig {
        case syscall.SIGHUP, syscall.SIGQUIT, syscall.SIGTERM, syscall.SIGINT:
            closeChan <- struct{}{}
        }
    }()

    listener, err := net.Listen("tcp", cfg.Address)
    if err != nil {
        return err
    }
    logger.Info(fmt.Sprintf("bind: %s, start listening...", cfg.Address))
    ListenAndServe(listener, handler, closeChan)
    return nil
}

func ListenAndServe(listener net.Listener, handler tcp.Handler, closeChan <-chan struct{}) {
    // listen signal
    go func() {
        <-closeChan
        logger.Info("shutting down")
        _ = listener.Close()
        _ = handler.Close()
    }()

    // listen port
    defer func() {
        _ = listener.Close()
        _ = handler.Close()
    }()

    ctx := context.Background()
    var waitDone sync.WaitGroup

    for {
        conn, err := listener.Accept()
        if err != nil {
            break
        }
        logger.Info("accepted link")
        waitDone.Add(1)
        go func() {
            defer func() {
                waitDone.Done()
            }()
            handler.Handle(ctx, conn)
        }()
    }

    waitDone.Wait()
}
