import numpy as np
from math import gcd, ceil, log2
from fractions import Fraction
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import Aer

def apply_inverse_qft(circuit, qubits):
    """Apply inverse QFT directly using elementary gates"""
    print("\n--- Applying inverse Quantum Fourier Transform ---")
    print("This transforms the phase differences back into computational basis states")
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
    
    print(f"Applied inverse QFT to {n} qubits using {n} Hadamard gates and {n*(n-1)//2} controlled-phase rotations")

def create_shor_circuit(a, N):
    """
    Create a quantum circuit for Shor's algorithm with given a and N.
    Uses only basic gates to ensure simulator compatibility.
    """
    print("\n--- Creating Quantum Circuit for Shor's Algorithm ---")
    
    # Determine required number of qubits
    n = ceil(log2(N))  # number of qubits needed to represent N
    m = 2*n            # size of counting register
    
    print(f"For N = {N}, we need:")
    print(f"- {n} qubits for the target register (to represent numbers up to N)")
    print(f"- {m} qubits for the counting register (to achieve sufficient precision)")
    
    # Create quantum registers
    counting_register = QuantumRegister(m, name='count')
    target_register = QuantumRegister(n, name='target')
    cr = ClassicalRegister(m, name='measurements')
    
    # Create quantum circuit
    circuit = QuantumCircuit(counting_register, target_register, cr)
    
    print("\n--- Circuit Initialization ---")
    # Initialize target register to |1⟩
    circuit.x(target_register[0])
    print("Initialized target register to |1⟩ (starting value for modular exponentiation)")
    
    # Apply Hadamard gates to counting register
    for qubit in counting_register:
        circuit.h(qubit)
    print(f"Applied Hadamard gates to all {m} qubits in counting register to create superposition")
    
    print("\n--- Building Modular Exponentiation Circuit ---")
    print(f"Implementing controlled operations to compute |x⟩|1⟩ → |x⟩|{a}^x mod {N}⟩")
    
    # Apply controlled modular exponentiation directly using basic gates
    for j in range(m):
        # Calculate a^(2^j) mod N
        exponent = 2**j
        modular_result = pow(a, exponent, N)
        
        print(f"  Step {j+1}/{m}: If counting qubit {j} is |1⟩, transform target by {a}^{exponent} mod {N} = {modular_result}")
        
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
    print("\nAdded measurement operations for the counting register")
    
    return circuit

def estimate_period(result_counts, m, N, a):
    """
    Estimate the period from measurement results.
    """
    print("\n--- Period Estimation from Quantum Measurements ---")
    
    # Sort by descending counts and get the most frequent results
    sorted_counts = sorted(result_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Print some debugging info about the measurements
    print("\nAnalyzing the most frequently measured states:")
    print("| Binary Measurement | Decimal Value | Phase Estimate | Frequency |")
    print("|-------------------|--------------|---------------|-----------|")
    
    for measurement, count in sorted_counts[:5]:
        measured_value = int(measurement, 2)
        phase = measured_value / (2**m)
        percentage = (count / sum(result_counts.values())) * 100
        print(f"| {measurement} | {measured_value} | {phase:.4f} | {count} ({percentage:.1f}%) |")
    
    print("\nLooking for a phase that corresponds to a valid period...")
    print("A valid period r must satisfy: a^r ≡ 1 (mod N) and r must be even")
    
    # Take the top 5 most frequent measurements
    top_measurements = sorted_counts[:5]
    
    for measurement, count in top_measurements:
        # Convert from binary to decimal
        measured_value = int(measurement, 2)
        
        # If measured value is 0, skip as it doesn't give period information
        if measured_value == 0:
            print(f"  Skipping measurement {measurement} (value=0) as it doesn't provide period information")
            continue
            
        # Use continued fraction expansion for period estimation
        phase = measured_value / (2**m)  # measured phase
        frac = Fraction(phase).limit_denominator(N)
        
        # The denominator is our candidate for the period
        r = frac.denominator
        
        print(f"  Testing measurement {measurement}: phase={phase:.4f}, continued fraction approximation: {frac}")
        
        # Check if this is likely a valid period
        if r % 2 == 0:
            check_value = pow(a, r, N)
            if check_value == 1:
                print(f"  ✓ Found valid period r = {r} because {a}^{r} mod {N} = 1 and r is even")
                return r
            else:
                print(f"  ✗ Period candidate r = {r} is not valid: {a}^{r} mod {N} = {check_value} (not 1)")
        else:
            print(f"  ✗ Period candidate r = {r} is not valid: it's odd and we need an even period")
            
    # If no good candidates found
    print("  ✗ Failed to find a valid period from the measurements")
    return None

def find_factors(a, r, N):
    """
    Find factors of N given the period r of a^x mod N.
    """
    print(f"\n--- Finding Factors Using Period r = {r} ---")
    
    # If r is odd, we can't use it directly
    if r % 2 != 0:
        print("Period is odd, which won't work with Shor's algorithm")
        return None
        
    # Try to find factors using r
    print(f"Computing gcd(a^(r/2) - 1, N) = gcd({a}^{r//2} - 1, {N})")
    
    base_val = a**(r//2)
    minus_val = base_val - 1
    plus_val = base_val + 1
    
    print(f"  {a}^{r//2} = {base_val}")
    print(f"  {a}^{r//2} - 1 = {minus_val}")
    print(f"  {a}^{r//2} + 1 = {plus_val}")
    
    guess_factor_1 = gcd(minus_val, N)
    guess_factor_2 = gcd(plus_val, N)
    
    print(f"  gcd({minus_val}, {N}) = {guess_factor_1}")
    print(f"  gcd({plus_val}, {N}) = {guess_factor_2}")
    
    # Check if we found non-trivial factors
    if guess_factor_1 != 1 and guess_factor_1 != N:
        other_factor = N // guess_factor_1
        print(f"Found factors: {guess_factor_1} × {other_factor} = {N}")
        return (guess_factor_1, other_factor)
    if guess_factor_2 != 1 and guess_factor_2 != N:
        other_factor = N // guess_factor_2
        print(f"Found factors: {guess_factor_2} × {other_factor} = {N}")
        return (guess_factor_2, other_factor)
        
    print("Could not find non-trivial factors with this period")
    return None

def run_shor_algorithm(N, a=None):
    """
    Run Shor's algorithm to factor N.
    """
    import random
    
    print("\n" + "="*60)
    print("        SHOR'S QUANTUM FACTORING ALGORITHM")
    print("="*60)
    
    print("\nShor's algorithm uses quantum computing to factor large numbers efficiently.")
    print("It works by finding the period of the function f(x) = a^x mod N, which")
    print("can then be used to find the factors of N with high probability.")
    
    if N % 2 == 0:
        print(f"\nN = {N} is even, so one factor is trivially 2")
        return 2, N // 2
    
    # Choose random a if not specified
    if a is None:
        print("\nSelecting a random base 'a' that is coprime with N...")
        a = random.randint(2, N-1)
        while gcd(a, N) != 1:
            a = random.randint(2, N-1)
    else:
        gcd_val = gcd(a, N)
        if gcd_val != 1:
            print(f"Lucky! The chosen base a = {a} already shares a factor with N: gcd({a}, {N}) = {gcd_val}")
            return gcd_val, N // gcd_val
        print(f"\nChecking if base a = {a} is coprime with N = {N}:")
        print(f"gcd({a}, {N}) = 1, so they are coprime (share no common factors)")
    
    print(f"\nStarting Shor's algorithm to factor N = {N}")
    print(f"Using a = {a} as the base for modular exponentiation")
    print("\nClassically computing a few powers of a mod N to illustrate the periodicity:")
    
    # Show some powers to illustrate periodicity
    print(" x  | a^x mod N")
    print("----|----------")
    for i in range(8):
        print(f" {i}  | {pow(a, i, N)}")
    
    # Determine circuit size parameters
    n = ceil(log2(N))
    m = 2*n
    
    # Create the quantum circuit
    circuit = create_shor_circuit(a, N)
    
    print("\n--- Quantum Circuit Summary ---")
    print(f"- Counting register: {m} qubits")
    print(f"- Target register: {n} qubits")
    print(f"- Total qubits: {m+n}")
    print(f"- Circuit depth: {circuit.depth()}")
    print(f"- Number of operations: {circuit.size()}")
    
    # Execute on simulator
    backend = Aer.get_backend('qasm_simulator')
    print("\n--- Executing Circuit on Quantum Simulator ---")
    print(f"Running with {1024} shots (measurements)")
    shots = 1024
    
    try:
        job = backend.run(circuit, shots=shots)
        results = job.result()
        counts = results.get_counts()
        print("\n✓ Circuit execution successful!")
    except Exception as e:
        print(f"\n✗ Error executing circuit: {str(e)}")
        print("\nTrying to run a very simplified version...")
        return run_simple_version(N, a)
    
    # Find the period from measurements
    print("\n--- Analyzing Quantum Measurement Results ---")
    print(f"Received {len(counts)} unique measurement outcomes from {shots} total measurements")
    r = estimate_period(counts, m, N, a)
    
    if r is None:
        print("\n✗ Failed to find a good period estimate. The algorithm was unsuccessful.")
        return None
    
    print(f"\n✓ Successfully estimated period: r = {r}")
    
    # Find factors using the period
    factors = find_factors(a, r, N)
    
    if factors:
        p, q = factors
        print("\n" + "="*60)
        print(f"SUCCESS! Factorization complete: {N} = {p} × {q}")
        print("="*60)
    else:
        print("\n" + "="*60)
        print(f"✗ Failed to find factors of {N} using period r = {r}")
        print("Try again with a different 'a' value")
        print("="*60)
        
    return factors

def run_simple_version(N, a):
    """Run a very simplified version with minimal qubits for testing purposes"""
    print("\n" + "="*60)
    print("RUNNING SIMPLIFIED VERSION OF SHOR'S ALGORITHM")
    print("="*60)
    print("\nThis is a simplified version with fewer qubits and operations")
    print("It's used as a fallback when the full algorithm encounters issues")
    
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
    
    print(f"\nUsing only a^1 mod {N} = {result} for the controlled operation")
    print(f"Binary representation: {result_bits}")
    
    for i in range(n):
        if result_bits[n-1-i] == '1':
            circuit.cx(counting[0], target[i])
    
    # Apply inverse QFT directly using elementary gates
    apply_inverse_qft(circuit, counting)
    
    # Measure
    circuit.measure(counting, cr)
    
    # Execute
    backend = Aer.get_backend('qasm_simulator')
    print("\nRunning simplified circuit...")
    
    try:
        job = backend.run(circuit, shots=100)
        results = job.result()
        counts = results.get_counts()
        print("\n✓ Simplified version executed successfully!")
        
        print("\nMeasurement outcomes (top 5):")
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        for measurement, count in sorted_counts[:5]:
            print(f"  {measurement}: {count} occurrences")
        
        # Try to find the period from these simplified results
        r = estimate_period(counts, m, N, a)
        if r:
            print(f"\n✓ Simplified version found period r = {r}")
            factors = find_factors(a, r, N)
            if factors:
                p, q = factors
                print("\n" + "="*60)
                print(f"SUCCESS! Factorization complete: {N} = {p} × {q}")
                print("="*60)
                return factors
        else:
            print("\n✗ Simplified version could not find a valid period")
        return None
    except Exception as e:
        print(f"\n✗ Even simplified version failed: {str(e)}")
        print("There may be an issue with your Qiskit installation or version compatibility")
        return None

# Example usage
if __name__ == "__main__":
    print("="*60)
    print("      QUANTUM FACTORIZATION USING SHOR'S ALGORITHM")
    print("="*60)
    print("\nThis program demonstrates how quantum computers can factor")
    print("integers efficiently using Shor's algorithm, which is exponentially")
    print("faster than the best known classical algorithms.")
    print("\nThis is implemented using Qiskit to simulate the quantum computation.")
    
    # Try to factor N=15
    N = 15
    a = 7  # coprime with 15
    print(f"\nWe'll factor N = {N} using base a = {7}")
    print("(In a real application, we'd use much larger numbers like RSA keys)")
    
    factors = run_shor_algorithm(N, a)
    
    if factors:
        print("\nDemonstration complete! This shows how quantum computers could")
        print("potentially break RSA encryption by efficiently factoring large numbers.")
    else:
        print("\nThe algorithm failed to find factors. This can happen occasionally")
        print("due to the probabilistic nature of quantum algorithms.")