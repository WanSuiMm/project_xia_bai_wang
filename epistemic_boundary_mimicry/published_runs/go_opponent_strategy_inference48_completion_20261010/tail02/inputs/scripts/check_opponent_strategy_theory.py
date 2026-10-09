"""Offline exact checks for THEORY_V2_20261009.md (standard library only)."""

from fractions import Fraction
from math import comb, isclose, pi, sqrt


def rising(n: int, k: int) -> int:
    """Rising factorial (n)_k for nonnegative integers."""
    value = 1
    for offset in range(k):
        value *= n + offset
    return value


def beta_sequence_probability(alpha: int, beta: int, ones: int, length: int) -> Fraction:
    """Posterior predictive probability of one ordered sequence with the given ones."""
    if not (0 <= ones <= length):
        raise ValueError("ones must be between zero and length")
    return Fraction(
        rising(alpha, ones) * rising(beta, length - ones),
        rising(alpha + beta, length),
    )


def persistent_history_p_a(history_ones: int) -> Fraction:
    alpha = 1 + history_ones
    beta = 9 - history_ones
    p_b_zero = beta_sequence_probability(alpha, beta, ones=0, length=4)
    p_b_one = beta_sequence_probability(alpha, beta, ones=4, length=4)
    return p_b_zero / (p_b_zero + p_b_one)


def plug_in_history_p_a(history_ones: int) -> Fraction:
    posterior_mean = Fraction(1 + history_ones, 10)
    p_b_zero = (1 - posterior_mean) ** 4
    p_b_one = posterior_mean**4
    return p_b_zero / (p_b_zero + p_b_one)


def exact_uniform_beta_risk_by_count_enumeration(rounds: int) -> Fraction:
    """Equal-prior error, enumerating count classes of both length-T records."""
    reader_one_sequence = Fraction(1, 1 << rounds)
    # Under b ~ Uniform(0, 1), a specified sequence with k ones has
    # integral_0^1 b^k (1-b)^(T-k) db = 1 / ((T+1) * choose(T,k)).
    bluffer_one_sequence = [
        Fraction(1, (rounds + 1) * comb(rounds, count))
        for count in range(rounds + 1)
    ]

    overlap = Fraction(0)
    for reader_count in range(rounds + 1):
        for bluffer_count in range(rounds + 1):
            multiplicity = comb(rounds, reader_count) * comb(rounds, bluffer_count)
            under_reader_a = reader_one_sequence * bluffer_one_sequence[bluffer_count]
            under_reader_b = bluffer_one_sequence[reader_count] * reader_one_sequence
            overlap += multiplicity * min(under_reader_a, under_reader_b)
    return overlap / 2


def uniform_beta_closed_form(rounds: int) -> Fraction:
    expected_abs = sum(
        Fraction(comb(rounds, count), 1 << rounds)
        * abs(Fraction(count) - Fraction(rounds, 2))
        for count in range(rounds + 1)
    )
    central_mass = (
        Fraction(comb(rounds, rounds // 2), 1 << rounds)
        if rounds % 2 == 0
        else Fraction(0)
    )
    return (
        2 * expected_abs / (rounds + 1)
        + central_mass / (2 * (rounds + 1))
    )


def binary_sequence_risk(rounds: int, bluffer_likelihoods: list[Fraction]) -> Fraction:
    reader_likelihood = Fraction(1, 1 << rounds)
    overlap = Fraction(0)
    for count_a in range(rounds + 1):
        for count_b in range(rounds + 1):
            multiplicity = comb(rounds, count_a) * comb(rounds, count_b)
            under_a_reader = reader_likelihood * bluffer_likelihoods[count_b]
            under_b_reader = bluffer_likelihoods[count_a] * reader_likelihood
            overlap += multiplicity * min(under_a_reader, under_b_reader)
    return overlap / 2


def check_persistent_refreshed_toy() -> None:
    for rounds in range(1, 31):
        fair = Fraction(1, 1 << rounds)
        persistent = [
            Fraction(1, 2) if count in (0, rounds) else Fraction(0)
            for count in range(rounds + 1)
        ]
        refreshed = [fair] * (rounds + 1)
        assert binary_sequence_risk(rounds, persistent) == Fraction(1, 1 << rounds)
        assert binary_sequence_risk(rounds, refreshed) == Fraction(1, 2)


def main() -> None:
    expected_persistent = {
        1: Fraction(66, 67),
        4: Fraction(1, 2),
        7: Fraction(1, 67),
    }
    expected_plugin = {
        1: Fraction(256, 257),
        4: Fraction(1, 2),
        7: Fraction(1, 257),
    }

    print("History s/8 | exact predictive P(K=A) | posterior-mean plug-in")
    for history_ones in (1, 4, 7):
        exact = persistent_history_p_a(history_ones)
        plug_in = plug_in_history_p_a(history_ones)
        assert exact == expected_persistent[history_ones]
        assert plug_in == expected_plugin[history_ones]
        assert persistent_history_p_a(8 - history_ones) == 1 - exact
        print(
            f"{history_ones}/8 | {float(exact):.10f} ({exact}) | "
            f"{float(plug_in):.10f} ({plug_in})"
        )

    for history_ones in range(9):
        assert persistent_history_p_a(history_ones) + persistent_history_p_a(
            8 - history_ones
        ) == 1

    refreshed_zero = beta_sequence_probability(1, 1, ones=0, length=4)
    refreshed_one = beta_sequence_probability(1, 1, ones=4, length=4)
    assert refreshed_zero == refreshed_one == Fraction(1, 5)
    for _history_ones in range(9):
        assert refreshed_zero / (refreshed_zero + refreshed_one) == Fraction(1, 2)
    print("Refreshed current-game predictive: P(0000)=P(1111)=1/5; P(K=A)=0.5")

    check_persistent_refreshed_toy()
    print("Persistent/refreshed repeated-bit toy: exact risks matched for T=1..30")

    for rounds in range(1, 31):
        enumerated = exact_uniform_beta_risk_by_count_enumeration(rounds)
        closed_form = uniform_beta_closed_form(rounds)
        assert enumerated == closed_form, (rounds, enumerated, closed_form)

    t = 30
    risk_t = exact_uniform_beta_risk_by_count_enumeration(t)
    scaled = float(risk_t) * sqrt(t)
    limit_constant = sqrt(2 / pi)
    assert isclose(scaled, limit_constant, rel_tol=0.20)
    print("Uniform-Beta exact risk identity: matched by count enumeration for T=1..30")
    print(
        f"T=30: risk={float(risk_t):.10f}; sqrt(T)*risk={scaled:.10f}; "
        f"asymptotic constant sqrt(2/pi)={limit_constant:.10f}"
    )
    print("All offline theory checks passed.")


if __name__ == "__main__":
    main()
