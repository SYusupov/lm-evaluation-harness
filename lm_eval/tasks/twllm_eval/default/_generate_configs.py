"""
Take in a YAML, and output all "other" splits with this YAML
"""
import argparse
import os

import pandas as pd
import yaml
from tqdm import tqdm


categories = {
    "localization": [
        "tw_truthful_qa",
    ],
}

task_list = [
    "tw_truthful_qa",
]
subject2name = {}
# subject2category = {}
SUBJECTS = {}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_yaml_path", default="_default_template_yaml")
    parser.add_argument("--save_prefix_path", default="twllm_eval")
    parser.add_argument("--cot_prompt_path", default=None)
    parser.add_argument("--task_prefix", default="")
    parser.add_argument("--group_prefix", default="")
    parser.add_argument("--subject_file", default="subject.tsv")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    from pathlib import Path

    # Initialization
    SUBJECT_FILE = Path(__file__).parent / Path(args.subject_file)

    df = pd.read_csv(SUBJECT_FILE, delimiter="\t")

    for _, row in df.iterrows():
        for _c in categories:
            if row["subject"] in SUBJECTS:
                raise ValueError("Duplicate tasks.")
            if row["category"] in categories[_c]:  # append new item into SUBJECTS
                SUBJECTS[row["subject"]] = _c
                subject2name[row["subject"]] = row["name"]
                break
    # End of SUBJECTS initialization

    # get filename of base_yaml so we can `"include": ` it in our "other" YAMLs.
    base_yaml_name = os.path.split(args.base_yaml_path)[-1]
    with open(args.base_yaml_path) as f:
        base_yaml = yaml.full_load(f)

    if args.cot_prompt_path is not None:
        import json

        with open(args.cot_prompt_path) as f:
            cot_file = json.load(f)

    ALL_CATEGORIES = []
    for subject, category in tqdm(SUBJECTS.items()):
        if category not in ALL_CATEGORIES:
            ALL_CATEGORIES.append(category)

        if args.cot_prompt_path is not None:
            description = cot_file[subject]
        else:
            name_of_subject = subject2name[subject].replace("＿", " ")
            description = f"以下為{name_of_subject}的單選題，請提供正確答案的選項。\n\n"

        yaml_dict = {
            "include": base_yaml_name,
            "group": f"twllm_eval_{args.task_prefix}_{category}"
            if args.task_prefix != ""
            else f"twllm_eval_{category}",
            "group_alias": category.replace("_", " "),
            "task": f"twllm_eval_{args.task_prefix}_{subject}"
            if args.task_prefix != ""
            else f"twllm_eval_{subject}",
            "task_alias": subject.replace("_", " "),
            "dataset_name": subject,
            "description": description,
        }

        file_save_path = args.save_prefix_path + f"_{subject}.yaml"
        # eval_logger.info(f"Saving yaml for subset {subject} to {file_save_path}")
        with open(file_save_path, "w") as yaml_file:
            yaml.dump(
                yaml_dict,
                yaml_file,
                # width=float("inf"),
                allow_unicode=True,
                default_style='"',
            )

    if args.task_prefix != "":
        mmlu_subcategories = [
            f"twllm_eval_{args.task_prefix}_{category}" for category in ALL_CATEGORIES
        ]
    else:
        mmlu_subcategories = [f"twllm_eval_{category}" for category in ALL_CATEGORIES]

    if args.group_prefix != "":
        file_save_path = args.group_prefix + ".yaml"
    else:
        file_save_path = args.save_prefix_path + ".yaml"

    # eval_logger.info(f"Saving benchmark config to {file_save_path}")
    with open(file_save_path, "w") as yaml_file:
        yaml.dump(
            {
                "group": f"twllm_eval_{args.task_prefix}"
                if args.task_prefix != ""
                else "twllm_eval",
                "task": mmlu_subcategories,
            },
            yaml_file,
            indent=4,
            default_flow_style=False,
        )
