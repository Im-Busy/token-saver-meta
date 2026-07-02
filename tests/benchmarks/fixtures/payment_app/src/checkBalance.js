export function checkBalance(cardNumber, amount) {
  return cardNumber.startsWith('4') && amount < 1000;
}
