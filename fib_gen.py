import os

def fibonacci_generator(n):
    """Generates the first n Fibonacci numbers."""
    # Start with 0 and 1
    a, b = 0, 1
    result = []
    for _ in range(n):
        result.append(a)
        # Update a and b for the next number
        a, b = b, a + b
    return result

if __name__ == "__main__":
    N = 20
    fib_numbers = fibonacci_generator(N)

    # Prepare output for printing and file writing
    output_lines = [f"Fibonacci({i+1}): {num}" for i, num in enumerate(fib_numbers)]
    output_content = "\n".join(output_lines)

    # 1. Print to console
    print("--- Fibonacci Sequence (First 20) ---")
    print(output_content)
    print("------------------------------------")

    # 2. Save to file
    file_path = "results/fibonacci.txt"
    directory = os.path.dirname(file_path)

    # Ensure the 'results' directory exists
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

    try:
        with open(file_path, "w") as f:
            f.write("Fibonacci Sequence (First 20)\n")
            f.write("==============================\n")
            f.write(output_content)
            f.write("\n") # Ensure a final newline
        print(f"\nSuccessfully wrote results to {file_path}")
    except Exception as e:
        print(f"Error writing to file: {e}")
