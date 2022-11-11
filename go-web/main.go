package main

import (
	"gee"
	"net/http"
)

func main() {
	r := gee.Default()
	r.GET("/", func(ctx *gee.Context) {
		ctx.String(http.StatusOK, "Hello Tesla\n")
	})
	r.GET("/panic", func(ctx *gee.Context) {
		names := []string{"tesla"}
		ctx.String(http.StatusOK, names[2])
	})
	r.Run(":9999")
}
