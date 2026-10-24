# test_cli.py
# part of Arcturus, a programming language and compiler for the Infocom Z-machine.
# Copyright (c) 2026, Stefan Vogt.
# https://github.com/ByteProject/Arcturus

"""The arcc command line, run as a real process."""

def test_no_cosmos_still_merges_the_games_own_chapters(tmp_path):
    # auraes (2026-10-23): with --no-cosmos every summon was skipped, so a
    # chapter's declarations silently vanished. Chapters merge; a granule
    # summon is refused by name.
    import subprocess, sys, os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    (tmp_path / "rooms.storyarc").write_text('room yard\n    name "Yard"\n')
    main = tmp_path / "main.storyarc"
    main.write_text('summon rooms.storyarc\ngame\n    title "N"\n    start hall\n'
                    'room hall\n    name "Hall"\n    desc "A hall."\n    north yard\n')
    env = dict(os.environ, PYTHONPATH=root)
    run = subprocess.run([sys.executable, "-m", "arcturus.cli", str(main), "--no-cosmos",
                          "-q", "-o", str(tmp_path / "n.z5")], capture_output=True,
                         text=True, env=env, cwd=tmp_path)
    assert run.returncode == 0, run.stderr
    main.write_text("summon.statusline\n" + main.read_text())
    run = subprocess.run([sys.executable, "-m", "arcturus.cli", str(main), "--no-cosmos",
                          "-q", "-o", str(tmp_path / "n.z5")], capture_output=True,
                         text=True, env=env, cwd=tmp_path)
    assert run.returncode != 0 and "cannot summon a granule" in run.stderr
