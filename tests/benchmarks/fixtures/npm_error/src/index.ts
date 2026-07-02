function greet(name: string): string {
  return "Hello, " + name.toUpperCase();
}

const result: number = greet("World"); // ERROR: string assigned to number
console.log(result);
