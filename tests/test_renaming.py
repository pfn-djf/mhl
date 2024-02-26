"""
__author__ = "Katharina Böttcher"
__copyright__ = "Copyright 2024, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""

import os
from click.testing import CliRunner
from freezegun import freeze_time

import ascmhl


@freeze_time("2020-01-16 09:15:00")
def test_verify_renamed_files(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert not result.exception

    os.rename("/root/A/AA/AA1.txt", "/root/A/AA/AA1_renamed.txt")
    with open("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl", "r+") as f:
        contents = f.readlines()
        for index, line in enumerate(contents):
            if "A/AA/AA1.txt" in line:
                contents.remove(line)
                new_line = line.replace("A/AA/AA1.txt", "A/AA/AA1_renamed.txt")
                contents.insert(index, new_line)
                contents.insert(index + 2, "<previousPath>A/AA/AA1.txt</previousPath>")
                break

        f.seek(0)
        f.writelines(contents)

    with open("/root/ascmhl/ascmhl_chain.xml", "r+") as f:
        contents = f.readlines()
        for index, line in enumerate(contents):
            if "0002" in line:
                hash_line = contents.pop(index + 1)
                contents.insert(
                    index + 1,
                    hash_line.replace(
                        "c45azZxqkrhs2TgYjDAB5k7zPYJNytvtsdgSuUtkNa4cRb9YJhvcR7zmfRM5avixb1tw9xrURQh477Ht4J8byfAUQu",
                        "c441eqmCwPf2QS3yCJAGAcV9kB8WiKCMGoVVWvPv834q4HUpNZkMnti9yPuMKzQgMmEVFNEV84vJtHCZaoWJfU6qqq",
                    ),
                )
        f.seek(0)
        f.writelines(contents)

    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert not result.exception

    result = runner.invoke(ascmhl.commands.info, ["-sf", "/root/A/AA/AA1_renamed.txt", "-v", "/root"])
    assert not result.exception
    assert result.output.count("AA1.txt") == 3
    assert result.output.count("AA1_renamed.txt") == 3
    assert result.output.count("Generation 2") == 2


@freeze_time("2020-01-16 09:15:00")
def test_verify_renamed_file_but_also_changed_file(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert not result.exception

    os.rename("/root/A/AA/AA1.txt", "/root/A/AA/AA1_renamed.txt")
    with open("/root/A/AA/AA1_renamed.txt", "a") as f:
        f.write("change file")
    with open("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl", "r+") as f:
        contents = f.readlines()
        for index, line in enumerate(contents):
            if "A/AA/AA1.txt" in line:
                contents.remove(line)
                new_line = line.replace("A/AA/AA1.txt", "A/AA/AA1_renamed.txt")
                contents.insert(index, new_line)
                contents.insert(index + 2, "<previousPath>A/AA/AA1.txt</previousPath>")
                break
        f.seek(0)
        f.writelines(contents)

    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert result.exception


@freeze_time("2020-01-16 09:15:00")
def test_detect_renamed_files(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert not result.exception

    os.rename("/root/A/AA/AA1.txt", "/root/A/AA/AA1_renamed.txt")
    fs.create_file("/root/B/B2.txt", contents="B2\n")

    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v", "-dr"])
    assert not result.exception

    with open("/root/ascmhl/0003_root_2020-01-16_091500Z.mhl", "r") as fin:
        fileContents = fin.read()
        assert fileContents.count("previousPath") == 2
        assert "AA1.txt" in fileContents
        assert "AA1_renamed.txt" in fileContents

    result = runner.invoke(ascmhl.commands.verify, ["/root", "-h", "xxh64"])
    assert not result.exception


@freeze_time("2020-01-16 09:15:00")
def test_detect_renamed_files_different_hash(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert not result.exception

    os.rename("/root/A/AA/AA1.txt", "/root/A/AA/AA1_renamed.txt")
    fs.create_file("/root/B/B2.txt", contents="B2\n")

    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-dr"])
    assert not result.exception

    with open("/root/ascmhl/0003_root_2020-01-16_091500Z.mhl", "r") as fin:
        fileContents = fin.read()
        assert fileContents.count("previousPath") == 2
        assert "AA1.txt" in fileContents
        assert "AA1_renamed.txt" in fileContents

    result = runner.invoke(ascmhl.commands.verify, ["/root", "-h", "xxh64"])
    assert not result.exception


@freeze_time("2020-01-16 09:15:00")
def test_detect_renamed_files_different_hash(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert not result.exception

    os.rename("/root/A/AA/AA1.txt", "/root/A/AA/AA1_renamed.txt")
    fs.create_file("/root/B/B2.txt", contents="B2\n")

    result = runner.invoke(ascmhl.commands.create, ["/root", "-v", "-dr"])
    assert not result.exception

    with open("/root/ascmhl/0003_root_2020-01-16_091500Z.mhl", "r") as fin:
        fileContents = fin.read()
        assert fileContents.count("previousPath") == 2
        assert "AA1.txt" in fileContents
        assert "AA1_renamed.txt" in fileContents

    result = runner.invoke(ascmhl.commands.verify, ["/root", "-h", "xxh64"])
    assert not result.exception


@freeze_time("2020-01-16 09:15:00")
def test_do_not_detect_renamed_files(fs):
    fs.create_file("/root/Stuff.txt", contents="stuff\n")
    fs.create_file("/root/A/A1.txt", contents="A1\n")
    fs.create_file("/root/B/B1.txt", contents="B1\n")
    fs.create_file("/root/A/AA/AA1.txt", contents="AA1\n")

    runner = CliRunner()
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert not result.exception
    assert os.path.exists("/root/ascmhl/0002_root_2020-01-16_091500Z.mhl")
    assert os.path.exists("/root/ascmhl/ascmhl_chain.xml")
    result = runner.invoke(ascmhl.commands.verify, ["/root"])
    assert not result.exception

    os.rename("/root/A/AA/AA1.txt", "/root/A/AA/AA1_renamed.txt")
    fs.create_file("/root/B/B2.txt", contents="B2\n")

    result = runner.invoke(ascmhl.commands.create, ["/root", "-h", "xxh64", "-v"])
    assert result.exception
