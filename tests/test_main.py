from md_man.main import parse_args


def test_parse_args_reads_root_path():
    args = parse_args(["/tmp/docs"])
    assert str(args.root_path) == "/tmp/docs"
