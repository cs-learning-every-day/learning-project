package xmorm

import (
	"errors"
	"testing"
	"xmorm/session"

	_ "github.com/mattn/go-sqlite3"
)

func OpenDB(t *testing.T) *Engine {
	t.Helper()
	engine, err := NewEngine("sqlite3", "xm.db")
	if err != nil {
		t.Fatal("failed to connect", err)
	}
	return engine
}

type User struct {
	Name string `xmorm:"PRIMARY KEY"`
	Age  int
}

func transactionRollBack(t *testing.T) {
	engine := OpenDB(t)
	defer engine.Close()

	s := engine.NewSession()
	_ = s.Model(&User{}).DropTable()
	_, err := engine.Transaction(func(s *session.Session) (result interface{}, err error) {
		_ = s.Model(&User{}).CreateTable()
		_, err = s.Insert(&User{"Tom", 18})
		return nil, errors.New("Error")
	})
	if err == nil || s.HasTable() {
		t.Fatal("failed to rollBack")
	}
}

func transactionCommit(t *testing.T) {
	engine := OpenDB(t)
	defer engine.Close()

	s := engine.NewSession()
	_ = s.Model(&User{}).DropTable()
	_, err := engine.Transaction(func(s *session.Session) (result interface{}, err error) {
		_ = s.Model(&User{}).CreateTable()
		_, err = s.Insert(&User{"Tom", 18})
		return
	})
	u := &User{}
	_ = s.First(u)
	if err != nil || u.Name != "Tom" {
		t.Fatal("failed to commit")
	}
}

func TestEngine_Transcation(t *testing.T) {
	t.Run("rollback", func(t *testing.T) {
		transactionRollBack(t)
	})
	t.Run("commit", func(t *testing.T) {
		transactionCommit(t)
	})
}

func TestNewEngine(t *testing.T) {
	engine := OpenDB(t)
	defer engine.Close()
}
