const wrapper: React.CSSProperties = {
  fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif',
  background: '#0b0d11',
  color: '#e7e9ee',
  minHeight: '100vh',
  display: 'grid',
  placeItems: 'center',
  padding: '24px',
};

const card: React.CSSProperties = {
  maxWidth: 560,
  padding: 32,
  borderRadius: 16,
  background: '#15181f',
  border: '1px solid #232733',
};

export default function App() {
  return (
    <div style={wrapper}>
      <div style={card}>
        <h1 style={{ marginTop: 0 }}>Cashlibot Admin</h1>
        <p style={{ color: '#a8acb8' }}>
          Admin dashboard scaffold. Real screens land after the backend admin
          API is wired up.
        </p>
      </div>
    </div>
  );
}
