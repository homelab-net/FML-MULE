# TAK cold start

systemd starts `opentakserver.target` for an unprivileged account.
`Notify=healthy` holds PostgreSQL, RabbitMQ, the API, and the listener
until their probes pass. The parser has no listen port; the persisted
row is its proof. The target only wants the API at runtime. Both workers
perform a one-time active check after the API start job, so forced API
startup failure must keep them closed. The script does not start the five
containers.

The mesh-gate unit on this runner is a stand-in with the unresolved
name. It is held closed until the members are observed waiting. That is
not `TBR-LINUX-01` closing. The host is not given port 8081 or 8088.
Media stays off.

After a successful start, stopping only the API must leave the target,
listener, and parser active. Stopping the target and starting it again
must leave the row. That is not `Restart=` and not a different-node
restore. The account is not the field user. Rootless here means the user
namespace, including where an image entrypoint starts as uid 0 and then
drops.
