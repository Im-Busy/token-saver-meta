const express = require('express');
const app = express();
app.use(express.json());

app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  const user = findUser(username); // returns null if not found
  const email = user.email.toLowerCase(); // BUG: user may be null
  res.json({ email, loggedIn: true });
});

function findUser(username) {
  if (username === 'admin') return { email: 'admin@test.com' };
  return null;
}

app.listen(3000, () => console.log('Auth API on 3000'));
