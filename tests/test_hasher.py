from app.infrastructure.security.hasher import HasherPBKDF2


def test_hash_verifica_y_no_guarda_texto_plano():
    h = HasherPBKDF2(iteraciones=1000)
    guardado = h.hash("miClave")
    assert "miClave" not in guardado
    assert h.verificar("miClave", guardado) and not h.verificar("otra", guardado)
    assert h.hash("miClave") != guardado            # sal distinta cada vez
    assert not h.verificar("x", "basura")
