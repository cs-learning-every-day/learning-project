package main

import "fmt"

type User struct {
	Name string
}

func update(u *User) {
	u.Name = "Tesla"
}

func main() {
	var u User
	update(&u)
	fmt.Println(u.Name)
}
