import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def fnv1a(data_str: str) -> int:
    """
    FNV-1a 32-bit hash implementation in Python. This is a hashing function
    used by the pseudo-random number generator.
    """
    hash_val = 0x811C9DC5
    fnv_prime = 0x01000193
    for byte in data_str.encode("utf-8"):
        hash_val ^= byte
        hash_val = (hash_val * fnv_prime) & 0xFFFFFFFF
    return hash_val


def prng(seed: str, length: int) -> str:
    """
    Pseudo-random number generator, ported from the provided JavaScript. This
    function is used to generate the 'salt' and 'target' for each challenge.
    """
    state = fnv1a(seed)
    result = ""

    def next_val():
        nonlocal state
        state ^= state << 13
        state &= 0xFFFFFFFF
        state ^= state >> 17
        state &= 0xFFFFFFFF
        state ^= state << 5
        state &= 0xFFFFFFFF
        return state

    while len(result) < length:
        rnd = next_val()
        result += format(rnd, "08x")

    return result[:length]


def solve_pow(salt: str, target: str) -> int:
    """
    Solves the proof-of-work challenge. It iteratively tries different 'nonce'
    values until it finds a SHA-256 hash that starts with the 'target' string.
    """
    nonce = 0
    while True:
        attempt = salt + str(nonce)
        h = hashlib.sha256(attempt.encode("utf-8")).hexdigest()
        if h.startswith(target):
            return nonce
        nonce += 1


def solve_challenge(challenge_token: str, c: int, s: int, d: int) -> list[int]:
    """
    This is the main function that orchestrates the solving of the CAPTCHA.
    It generates all the necessary challenges and uses a thread pool to solve
    them in parallel, which significantly speeds up the process.

    Args:
        challenge_token: The token from the /api/cap/challenge endpoint.
        c: The number of challenges to solve.
        s: The salt size.
        d: The difficulty (length of the target prefix).

    Returns:
        A list of nonces, one for each solved challenge.
    """
    challenges = []
    for i in range(1, c + 1):
        salt = prng(f"{challenge_token}{i}", s)
        target = prng(f"{challenge_token}{i}d", d)
        challenges.append((salt, target))

    results = [0] * c
    with ThreadPoolExecutor() as executor:
        # Create a mapping from future to its index to maintain order
        future_to_index = {
            executor.submit(solve_pow, salt, target): i
            for i, (salt, target) in enumerate(challenges)
        }
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                nonce = future.result()
                results[index] = nonce
            except Exception as exc:
                print(f"Challenge {index} generated an exception: {exc}")

    return results
