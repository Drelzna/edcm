^w::
    pips_240()
    exit

^a::
    pips_402()
    exit

; pips 2-0-4
^d::
    pips_204()
    exit

; pips 3-0-3
^s::
    pips_303()
    exit

; power to engines
pips_240() {
    Send {Down},{Left},{Left},{Up},{Up},{Up}
    return
}

; power to sheilds
pips_402() {
    Send {Down},{Right},{Left},{Left},{Left}
    return
}

; power to weapons
pips_204() {
    Send {Down},{Left},{Right},{Right},{Right}
    return
}

; power shields and weapons
pips_303() {
    Send {Down},{Right},{Left},{Right},{Left},{Right},{Left}
    return
}

^j::
setkeydelay, 30, 30
send, g
sleep, 1000
send, e
sleep, 20
send, {Enter}
sleep, 20
send, ^v
send, {Enter}
sleep, 3000
send, {Enter}
sleep, 20
send, g
exit