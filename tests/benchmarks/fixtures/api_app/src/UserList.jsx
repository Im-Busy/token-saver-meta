import React from 'react';

export default function UserList() {
  const [users, setUsers] = React.useState([]);
  React.useEffect(() => {
    fetch('/api/users').then(r => r.json()).then(d => setUsers(d.users));
  }, []);
  return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
