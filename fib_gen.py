import os

def fibonacci_sequence(n):
    """Generates the first n Fibonacci numbers."""
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence

def main():
    N = 20
    fib_numbers = fibonacci_sequence(N)

    # Convert numbers to strings for easy printing/saving
    fib_output = [str(num) for num in fib_numbers]
    output_content = "\n".join(fib_output)

    # 1. Print to console
    print(f"Fibonacci Sequence (first {N} numbers):")
    print(output_content)

    # 2. Save to file
    output_dir = 'results'
    output_path = os.path.join(output_dir, 'fibonacci.txt')

    # Ensure the directory exists
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            f.write(output_content + "\n")
        print(f"\nSuccessfully saved the sequence to {output_path}")
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    main()
