import numpy as np
from math import gcd, ceil, log2
from fractions import Fraction
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import Aer

def apply_inverse_qft(circuit, qubits):
    """Apply inverse QFT directly using elementary gates"""
    n = len(qubits)
    
    # Swap qubits
    for i in range(n//2):
        circuit.swap(qubits[i], qubits[n-i-1])
    
    # Apply rotations
    for j in range(n):
        circuit.h(qubits[j])
        for k in range(j+1, n):
            angle = -np.pi / float(2**(k-j))
            circuit.cp(angle, qubits[k], qubits[j])

def create_shor_circuit(a, N):
    """
    Create a quantum circuit for Shor's algorithm with given a and N.
    Uses only basic gates to ensure simulator compatibility.
    """
    # Determine required number of qubits
    n = ceil(log2(N))  # number of qubits needed to represent N
    m = 2*n            # size of counting register
    
    # Create quantum registers
    counting_register = QuantumRegister(m, name='count')
    target_register = QuantumRegister(n, name='target')
    cr = ClassicalRegister(m, name='measurements')
    
    # Create quantum circuit
    circuit = QuantumCircuit(counting_register, target_register, cr)
    
    # Initialize target register to |1⟩
    circuit.x(target_register[0])
    
    # Apply Hadamard gates to counting register
    for qubit in counting_register:
        circuit.h(qubit)
    
    # Apply controlled modular exponentiation directly using basic gates
    for j in range(m):
        # Calculate a^(2^j) mod N
        exponent = 2**j
        modular_result = pow(a, exponent, N)
        
        # Binary representation of modular_result
        result_bits = bin(modular_result)[2:].zfill(n)
        
        # Apply controlled-X gates directly based on the bits that differ
        for i in range(n):
            bit_pos = n - 1 - i  # Reverse order for big endian
            if result_bits[bit_pos] == '1':
                circuit.cx(counting_register[j], target_register[i])
    
    # Apply inverse QFT to counting register using elementary gates
    apply_inverse_qft(circuit, counting_register)
    
    # Measure the counting register
    circuit.measure(counting_register, cr)
    
    return circuit

def estimate_period(result_counts, m, N, a):
    """
    Estimate the period from measurement results.
    """
    # Sort by descending counts and get the most frequent results
    sorted_counts = sorted(result_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Print some debugging info about the measurements
    print("\nTop 5 measurement results:")
    for measurement, count in sorted_counts[:5]:
        measured_value = int(measurement, 2)
        phase = measured_value / (2**m)
        print(f"  {measurement} ({measured_value}) with {count} counts, phase ≈ {phase:.4f}")
    
    # Take the top 5 most frequent measurements
    top_measurements = sorted_counts[:5]
    
    for measurement, count in top_measurements:
        # Convert from binary to decimal
        measured_value = int(measurement, 2)
        
        # If measured value is 0, skip as it doesn't give period information
        if measured_value == 0:
            continue
            
        # Use continued fraction expansion for period estimation
        phase = measured_value / (2**m)  # measured phase
        frac = Fraction(phase).limit_denominator(N)
        
        # The denominator is our candidate for the period
        r = frac.denominator
        
        # Check if this is likely a valid period
        if r % 2 == 0 and pow(a, r, N) == 1:
            return r
            
    # If no good candidates found
    return None

def find_factors(a, r, N):
    """
    Find factors of N given the period r of a^x mod N.
    """
    # If r is odd, we can't use it directly
    if r % 2 != 0:
        return None
        
    # Try to find factors using r
    guess_factor_1 = gcd(a**(r//2) - 1, N)
    guess_factor_2 = gcd(a**(r//2) + 1, N)
    
    # Check if we found non-trivial factors
    if guess_factor_1 != 1 and guess_factor_1 != N:
        return (guess_factor_1, N // guess_factor_1)
    if guess_factor_2 != 1 and guess_factor_2 != N:
        return (guess_factor_2, N // guess_factor_2)
        
    return None

def run_shor_algorithm(N, a=None):
    """
    Run Shor's algorithm to factor N.
    """
    import random
    
    if N % 2 == 0:
        return 2, N // 2
    
    # Choose random a if not specified
    if a is None:
        a = random.randint(2, N-1)
        while gcd(a, N) != 1:
            a = random.randint(2, N-1)
    
    print(f"Running Shor's algorithm to factor N = {N}")
    print(f"Using a = {a} as the base for modular exponentiation")
    
    # Determine circuit size parameters
    n = ceil(log2(N))
    m = 2*n
    
    # Create the quantum circuit
    circuit = create_shor_circuit(a, N)
    
    print("\nCircuit summary:")
    print(f"- Counting register: {m} qubits")
    print(f"- Target register: {n} qubits")
    print(f"- Total qubits: {m+n}")

    print("\nCircuit depth:", circuit.depth())
    print("Number of operations:", circuit.size())
    
    # Execute on simulator
    backend = Aer.get_backend('qasm_simulator')
    print("\nExecuting circuit on quantum simulator...")
    shots = 1024
    
    try:
        job = backend.run(circuit, shots=shots)
        results = job.result()
        counts = results.get_counts()
        print("\nCircuit execution successful!")
    except Exception as e:
        print(f"Error executing circuit: {str(e)}")
        print("\nTrying to run a very simplified version...")
        return run_simple_version(N, a)
    
    # Find the period from measurements
    print("\nAnalyzing measurement results...")
    print(f"Total unique outcomes: {len(counts)}")
    r = estimate_period(counts, m, N, a)
    
    if r is None:
        print("Failed to find a good period estimate.")
        return None
    
    print(f"Estimated period: r = {r}")
    
    # Find factors using the period
    print("\nAttempting to find factors using period...")
    factors = find_factors(a, r, N)
    
    if factors:
        print(f"Success! Factors of {N} = {factors[0]} × {factors[1]}")
    else:
        print("Failed to find factors. Try again with a different 'a'.")
        
    return factors

def run_simple_version(N, a):
    """Run a very simplified version with minimal qubits for testing purposes"""
    print("Running extremely simplified version with just one controlled operation")
    
    n = ceil(log2(N))
    # Use smaller counting register
    m = n + 1
    
    # Create registers
    counting = QuantumRegister(m, 'c')
    target = QuantumRegister(n, 't')
    cr = ClassicalRegister(m, 'm')
    
    # Create circuit
    circuit = QuantumCircuit(counting, target, cr)
    
    # Initialize target to |1⟩
    circuit.x(target[0])
    
    # Apply H to counting register
    for qubit in counting:
        circuit.h(qubit)
    
    # Apply a single controlled operation for testing
    result = pow(a, 1, N)
    result_bits = bin(result)[2:].zfill(n)
    
    for i in range(n):
        if result_bits[n-1-i] == '1':
            circuit.cx(counting[0], target[i])
    
    # Apply inverse QFT directly using elementary gates
    apply_inverse_qft(circuit, counting)
    
    # Measure
    circuit.measure(counting, cr)
    
    # Execute
    backend = Aer.get_backend('qasm_simulator')
    print("Running simplified circuit...")
    
    try:
        job = backend.run(circuit, shots=100)
        results = job.result()
        counts = results.get_counts()
        print("Simplified version succeeded!")
        print("Measurement outcomes:", counts)
        
        # Try to find the period from these simplified results
        r = estimate_period(counts, m, N, a)
        if r:
            print(f"Simplified version found period r = {r}")
            factors = find_factors(a, r, N)
            if factors:
                print(f"Factors: {factors[0]} × {factors[1]}")
                return factors
        return None
    except Exception as e:
        print(f"Even simplified version failed: {str(e)}")
        print("There may be an issue with your Qiskit installation or version compatibility")
        return None

# Example usage
if __name__ == "__main__":
    # Try to factor N=15
    N = 15
    a = 7  # coprime with 15
    factors = run_shor_algorithm(N, a)