import subprocess
import tempfile
import os
from itertools import permutations
import time
import random

def run_python_code(filepath, input_str):
    try:
        result = subprocess.run(
            ["python3", filepath],
            input=input_str.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3
        )
        if result.returncode != 0:
            return None, result.stderr.decode()
        return result.stdout.decode().strip(), None
    except Exception as e:
        return None, str(e)

def run_cpp_code(filepath, input_str):

    tmp_root = "/path/to/testingsystemp/tmp_exec"
    os.makedirs(tmp_root, exist_ok=True)

    unique_id = f"{int(time.time() * 1000)}_{random.randint(1000,9999)}"
    tmpdir = os.path.join(tmp_root, unique_id)
    os.makedirs(tmpdir, exist_ok=True)

    exe_path = os.path.join(tmpdir, "prog")

    compile_result = subprocess.run(
        ["g++", filepath, "-o", exe_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5
    )
    if compile_result.returncode != 0:
        return None, compile_result.stderr.decode()

    os.chmod(exe_path, 0o755)

    try:
        result = subprocess.run(
            [exe_path],
            input=input_str.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3
        )
        if result.returncode != 0:
            return None, result.stderr.decode()
        return result.stdout.decode().strip(), None
    except Exception as e:
        return None, str(e)

TASKS = {
    "compress_string": {
        "languages": ["py"],
        "tests": [
            {"input": "AABCCCDE\n", "output": "2AB3CDE"},
            {"input": "ABBBBBBDGGE\n", "output": "A6BD2GE"},
            {"input": "AABBCC\n", "output": "2A2B2C"},
            {"input": "ABC\n", "output": "ABC"},
            {"input": "ZZZZZZZZZZ\n", "output": "10Z"},
            {"input": "TTANGAAA\n", "output": "2TANG3A"},
            {"input": "GFSHDJGFGHHHHFHGHFDGJFGAKHJGFGHJKSDAJHKGFADHGKJHGAADBBBBBBB\n", "output": "GFSHDJGFG4HFHGHFDGJFGAKHJGFGHJKSDAJHKGFADHGKJHG2AD7B"},
            {"input": "BBBAJDSJJJJSAJDKXKKXX\n", "output": "3BAJDS4JSAJDKX2K2X"},
            {"input": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n", "output": "300A"},
            {"input": "ZZOSAAAAJFNNNAISS\n", "output": "2ZOS4AJF3NAI2S"},
            {"input": "AAABBBBBBBBBBBBBBBBBBBBBBBBBHHHHHHHHHHHHHHHSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSASDGAANNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN\n", "output": "3A25B15H100SASDG2A95N"},
            {"input": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXVVVVVLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLSSSSSSSSSSHGJFKSDNFJNFNNFIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII\n", "output": "40X5V55L10SHGJFKSDNFJNF2NF80I"},
            {"input": "ABCDEFGHHHHHAKKKK\n", "output": "ABCDEFG5HA4K"},
            {"input": "DEDDDDBFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\n", "output": "DE4DB33F"},
            {"input": "HEHGRTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTSSSST\n", "output": "HEHGR34T4ST"},
        ],
    },
    "date_format_converter": {
        "languages": ["py"],
        "tests": [
            {"input": "22/02/2024\n", "output": "20240222"},
            {"input": "01/01/2000\n", "output": "20000101"},
            {"input": "31/12/1999\n", "output": "19991231"},
            {"input": "12/12/2004\n", "output": "20041212"},
            {"input": "03/08/2003\n", "output": "20030803"},
            {"input": "23/09/2024\n", "output": "20240923"},
            {"input": "10/03/2013\n", "output": "20130310"},
            {"input": "10/12/1998\n", "output": "19981210"},
            {"input": "28/02/1999\n", "output": "19990228"},
            {"input": "03/07/1990\n", "output": "19900703"},
            {"input": "13/02/1993\n", "output": "19930213"},
            {"input": "04/05/1994\n", "output": "19940504"},
            {"input": "15/02/2015\n", "output": "20150215"},
            {"input": "22/09/2010\n", "output": "20100922"},
            {"input": "07/08/2001\n", "output": "20010807"},
            {"input": "24/09/2002\n", "output": "20020924"},
            {"input": "01/02/2011\n", "output": "20110201"},
            {"input": "08/08/2008\n", "output": "20080808"},
            {"input": "06/05/1993\n", "output": "19930506"},
            {"input": "31/05/2019\n", "output": "20190531"},
        ],
    },
    "math_expression": {
        "languages": ["cpp"],
        "tests": [
            {"input": "1\n2\n3\n", "output": str((1 + 2 - 3 // 1) + 3 * 1 * 1 - (1 + 2))},
            {"input": "2\n3\n4\n", "output": str((2 + 3 - 4 // 2) + 4 * 2 * 2 - (2 + 3))},
            {"input": "10\n5\n2\n", "output": str((10 + 5 - 2 // 10) + 2 * 10 * 10 - (10 + 5))},
            {"input": "2\n3\n13\n", "output": str((2 + 3 - 13 // 2) + 13 * 2 * 2 - (2 + 3))},
            {"input": "9\n6\n18\n", "output": str((9 + 6 - 18 // 9) + 18 * 9 * 9 - (9 + 6))},
            {"input": "2\n6\n8\n", "output": str((2 + 6 - 8 // 2) + 8 * 2 * 2 - (2 + 6))},
            {"input": "8\n16\n20\n", "output": str((8 + 16 - 20 // 8) + 20 * 8 * 8 - (8 + 16))},
            {"input": "5\n6\n9\n", "output": str((5 + 6 - 9 // 5) + 9 * 5 * 5 - (5 + 6))},
            {"input": "2\n3\n7\n", "output": str((2 + 3 - 7 // 2) + 7 * 2 * 2 - (2 + 3))},
            {"input": "6\n19\n20\n", "output": str((6 + 19 - 20 // 6) + 20 * 6 * 6 - (6 + 19))},
        ],
    },
    "pow_manual": {
        "languages": ["cpp"],
        "tests": [
            {"input": "2\n3\n", "output": "8"},
            {"input": "5\n0\n", "output": "1"},
            {"input": "3\n4\n", "output": "81"},
            {"input": "2\n16\n", "output": "65536"},
            {"input": "10\n2\n", "output": "100"},
            {"input": "1\n200000\n", "output": "1"},
            {"input": "329\n2\n", "output": "108241"},
            {"input": "0\n100\n", "output": "0"},
            {"input": "4\n5\n", "output": "1024"},
            {"input": "6\n3\n", "output": "216"},
            {"input": "7\n2\n", "output": "49"},
            {"input": "8\n6\n", "output": "262144"},
            {"input": "9\n4\n", "output": "6561"},
            {"input": "11\n3\n", "output": "1331"},
            {"input": "13\n5\n", "output": "371293"},

        ],
    },
    "permute_n": {
        "languages": ["py","cpp"],
        "tests": [
            {
                "input": "1\n",
                "output": "\n".join(
                    [str(t) for t in permutations(range(1, 2))]
                ).replace("(", "(").replace(")", ")"),
            },
            {
                "input": "2\n",
                "output": "\n".join(
                    [str(t) for t in permutations(range(1, 3))]
                ).replace("(", "(").replace(")", ")"),
            },
            {
                "input": "3\n",
                "output": "\n".join(
                    [str(t) for t in permutations(range(1, 4))]
                ).replace("(", "(").replace(")", ")"),
            },
            {
                "input": "4\n",
                "output": "\n".join(
                    [str(t) for t in permutations(range(1, 5))]
                ).replace("(", "(").replace(")", ")"),
            },
            {
                "input": "5\n",
                "output": "\n".join(
                    [str(t) for t in permutations(range(1, 6))]
                ).replace("(", "(").replace(")", ")"),
            },
            {
                "input": "6\n",
                "output": "\n".join(
                    [str(t) for t in permutations(range(1, 7))]
                ).replace("(", "(").replace(")", ")"),
            },
            {
                "input": "7\n",
                "output": "\n".join(
                    [str(t) for t in permutations(range(1, 8))]
                ).replace("(", "(").replace(")", ")"),
            },
            {
                "input": "8\n",
                "output": "\n".join(
                    [str(t) for t in permutations(range(1, 9))]
                ).replace("(", "(").replace(")", ")"),
            },
        ],
    },
}

def evaluate(task_id: str, filepath: str):
    print(f"[EVALUATE] Проверка файла {filepath} для задачи {task_id}")
    task = TASKS.get(task_id)
    if not task:
        return {"passed": 0, "total": 0, "details": []}

    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext not in task["languages"]:
        return {"passed": 0, "total": len(task["tests"]), "details": []}

    run_func = run_python_code if ext == "py" else run_cpp_code

    passed = 0
    total = len(task["tests"])
    details = []

    for test in task["tests"]:
        inp = test["input"]
        expected = test["output"]

        output, err = run_func(filepath, inp)
        print(f"[TEST] Вход: {inp.strip()} | Ожидаемый вывод: {expected.strip()} | Полученный вывод: {output.strip() if output else 'None'} | Ошибка: {err}")
        result_entry = {
            "input": inp,
            "expected": expected,
            "output": output if output else "",
            "error": err,
            "passed": False
        }

        if err is not None:
            print(f"[ERROR] При выполнении теста возникла ошибка: {err}")
            details.append(result_entry)
            continue

        if task_id == "permute_n":
            import ast

            try:
                actual = ast.literal_eval(output)
                expected = list(permutations(range(1, int(test["input"].strip()) + 1)))

                if actual == expected:
                    passed += 1
                    details.append({
                        "input": test["input"],
                        "expected": str(expected),
                        "output": str(actual),
                        "passed": True,
                        "error": None,
                    })
                    continue
                else:
                    details.append({
                        "input": test["input"],
                        "expected": str(expected),
                        "output": str(actual),
                        "passed": False,
                        "error": None,
                    })
                    continue
            except Exception as e:
                details.append({
                    "input": test["input"],
                    "expected": str(expected),
                    "output": output,
                    "passed": False,
                    "error": str(e),
                })
                continue


        if output.strip() == expected.strip():
            passed += 1
            result_entry["passed"] = True

        details.append(result_entry)

    return {"passed": passed, "total": total, "details": details}

