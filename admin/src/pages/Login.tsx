export function Login() {
  return (
    <div className="shell">
      <div className="card login">
        <h1>Cashlibot Admin</h1>
        <p>
          To sign in, open the Cashlibot bot on Telegram, send <code>/admin</code>,
          and tap the link the bot sends back.
        </p>
        <p style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>
          If nothing happens after sending <code>/admin</code>, your account
          isn't marked as an admin yet. Set <code>is_admin=true</code> on your
          user row and try again.
        </p>
      </div>
    </div>
  );
}
