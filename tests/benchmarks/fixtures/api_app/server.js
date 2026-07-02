const express = require('express');
const app = express();
app.get('/api/users', (req, res) => {
  res.json({ users: [{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }] });
});
app.listen(3000, () => console.log('API running on 3000'));
