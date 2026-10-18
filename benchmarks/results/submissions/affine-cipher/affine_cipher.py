from math import gcd


ALPHABET_SIZE = 26


def _validate_key(a):
    if gcd(a, ALPHABET_SIZE) != 1:
        raise ValueError("a and m must be coprime.")


def encode(plain_text, a, b):
    _validate_key(a)

    encoded = []
    for char in plain_text.lower():
        if char.isalpha() and "a" <= char <= "z":
            value = ord(char) - ord("a")
            encoded.append(chr((a * value + b) % ALPHABET_SIZE + ord("a")))
        elif char.isdigit():
            encoded.append(char)

    text = "".join(encoded)
    return " ".join(text[index:index + 5] for index in range(0, len(text), 5))


def decode(ciphered_text, a, b):
    _validate_key(a)

    inverse = pow(a, -1, ALPHABET_SIZE)
    decoded = []
    for char in ciphered_text.lower():
        if char.isalpha() and "a" <= char <= "z":
            value = ord(char) - ord("a")
            decoded.append(chr((inverse * (value - b)) % ALPHABET_SIZE + ord("a")))
        elif char.isdigit():
            decoded.append(char)

    return "".join(decoded)
