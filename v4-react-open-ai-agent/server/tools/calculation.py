# Equivalent of the perform_calculation function
def perform_calculation(operation, a, b):
    # Convert string inputs to integers if they're strings
    if isinstance(a, str):
        a = int(a)
    if isinstance(b, str):
        b = int(b)

    # Validating the operation
    if operation not in ["add", "subtract", "multiply", "divide"]:
        return f"Invalid operation: {operation}, should be among ['add', 'subtract', 'multiply', 'divide']"

    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            return "Division by zero"
        return a / b
