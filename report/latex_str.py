earthquake_formula = r'C = \frac{ABI}{R}'

earthquake_b_formula = r'B = B_1 \times N'

earthquake_b1 = r'''
  B1 = 
  \begin{cases}
    S_0 + (S - S_0 + 1) \times (T / T_0) & 0 < T < T_0 \\
    S + 1 & T_0 \leq T < T_s \\
    (S + 1) \times (T_s / T) & T > T_s
  \end{cases}
'''
earthquake_n1 = r'''
  N =
  \begin{cases}
    1 &  T < T_s \\
    0.7 \times \frac{T - T_s}{4 - T_s} + 1 & T_s \leq T < 4 \;\text{Sec} \\
    1.7 & T \geq 4 \;\text{Sec}
  \end{cases} \\
'''
earthquake_n2 = r'''
  N =
  \begin{cases}
    1 &  T < T_s \\
    0.4 \times \frac{T - T_s}{4 - T_s} + 1 & T_s \leq T < 4 \;\text{Sec} \\
    1.4 & T \geq 4 \;\text{Sec}
  \end{cases}
'''

