package cluster

import (
	"context"
	"errors"
	"go-redis/resp/client"

	pool "github.com/jolestar/go-commons-pool/v2"
)

type connectionFactory struct {
	Peer string
}

/**
 * Create a pointer to an instance that can be served by the
 * pool and wrap it in a PooledObject to be managed by the pool.
 *
 * return error if there is a problem creating a new instance,
 *    this will be propagated to the code requesting an object.
 */
func (c *connectionFactory) MakeObject(ctx context.Context) (*pool.PooledObject, error) {
	cln, err := client.MakeClient(c.Peer)
	if err != nil {
		return nil, err
	}
	cln.Start()
	return pool.NewPooledObject(cln), nil
}

/**
 * Destroys an instance no longer needed by the pool.
 */
func (c *connectionFactory) DestroyObject(ctx context.Context, object *pool.PooledObject) error {
	client, ok := object.Object.(*client.Client)
	if !ok {
		return errors.New("type mismatch")
	}
	client.Close()
	return nil
}

/**
 * Ensures that the instance is safe to be returned by the pool.
 *
 * return false if object is not valid and should
 *         be dropped from the pool, true otherwise.
 */
func (c *connectionFactory) ValidateObject(ctx context.Context, object *pool.PooledObject) bool {
	return true
}

/**
 * Reinitialize an instance to be returned by the pool.
 *
 * return error if there is a problem activating object,
 *    this error may be swallowed by the pool.
 */
func (c *connectionFactory) ActivateObject(ctx context.Context, object *pool.PooledObject) error {
	return nil
}

/**
 * Uninitialize an instance to be returned to the idle object pool.
 *
 * return error if there is a problem passivating obj,
 *    this exception may be swallowed by the pool.
 */
func (c *connectionFactory) PassivateObject(ctx context.Context, object *pool.PooledObject) error {
	return nil
}
