from jinja2 import Environment
import questionary

from traintrack.schema.job import JobRequest


_JOB_TEMPLATE = """
{
  "job": {
    "project": "{{project}}",
    "group": "{{group}}",
    "name": "{{name}}",
    "notes": "{{notes}}",
    "repo": "Hobot",
    "spec": {
      "branch": "{{branch}}",
      "config": "{{config_path}}",
      "overrides": {
        {% for key, value in overrides.items() -%}
        "{{key}}": "{{value}}"{% if not loop.last %},{% endif %}
        {% endfor -%}
      }
    }
  },
  "agent_blacklist": [
    {% for agent_name in agent_blacklist -%}
    "{{agent_name}}"{% if not loop.last %},{% endif %}
    {% endfor -%}
  ]
}
"""


def prompt_for_closing_gap_job() -> JobRequest | None:
    try:
        # Ask the user for the project name
        project = questionary.text("What is the project name?",
                                   default="ppg_locomotion").unsafe_ask()

        # Ask the user for the group name
        group = questionary.text("What is the group name?",
                                 default="locomotion").unsafe_ask()

        # Ask the user for the job name
        name = questionary.text("What is the job name?").unsafe_ask()

        # Ask the user for job notes
        notes = questionary.text("Enter job notes").unsafe_ask()

        # Ask the user for the branch name
        branch = questionary.text("What is the branch name?",
                                  default="experiment/closing_gap").unsafe_ask()

        # Ask the user for the config as JSON
        config_path = questionary.text("Enter the config path",
                                  default="hobot/locomotion/low_level/ppg_locomotion_conf.py").unsafe_ask()

        # ---------- Questions on Conf Params ----------

        # Robot
        robot_make = questionary.text("Robot Make", default="unitree").unsafe_ask()
        robot_model = questionary.text("Robot Model", default="go1").unsafe_ask()
        name = f"{robot_model}_{name}"

        # Whether enable randomization
        enable_randomization = questionary.confirm(
            "Do you want to enable randomization", default=True).unsafe_ask()

        # The power weight
        power_weight = questionary.text("Power Weight", default="8e-7").unsafe_ask()

        # The survival reward
        survival_reward = questionary.text("Survival reward", default="0.01").unsafe_ask()

        # The initial z
        initial_z = questionary.text("Initial z", default={
            "anymal_b": "0.58",
            "go1": "0.325",
        }[robot_model]).unsafe_ask()

        # Ask the user for overrides
        overrides = {
            "enable_randomization": "True" if enable_randomization else "False",
            "power_weight": power_weight,
            "survival_reward": survival_reward,
            "initial_robot_z": initial_z,
        }

        if robot_model != "go1":
            overrides["robot_make"] = f"'{robot_make}'"
            overrides["robot_model"] = f"'{robot_model}'"
        
        while True:
            key = questionary.text("Enter override key (leave blank to finish)").unsafe_ask()
            if not key:
                break
            value = questionary.text("Enter override value").unsafe_ask()
            overrides[key] = value

        env = Environment()
        template = env.from_string(_JOB_TEMPLATE)
        json = template.render(
            project=project,
            group=group,
            name=name,
            notes=notes,
            branch=branch,
            config_path=config_path,
            overrides=overrides,
        )
        return JobRequest.parse_raw(json)
    except KeyboardInterrupt:
        return None


def prompt_for_whole_body_job() -> JobRequest | None:
    try:
        # Ask the user for the project name
        project = questionary.text(
            "What is the project name?", default="ppg_whole_body"
        ).unsafe_ask()

        # Ask the user for the group name
        group = questionary.text(
            "What is the group name?", default="locomotion"
        ).unsafe_ask()

        # Ask the user for the job name
        name = questionary.text("What is the job name?").unsafe_ask()

        # Ask the user for job notes
        notes = questionary.text("Enter job notes").unsafe_ask()

        # Ask the user for the branch name
        branch = questionary.text(
            "What is the branch name?", default="experiment/closing_gap"
        ).unsafe_ask()

        # Ask the user for the config as JSON
        config_path = questionary.text(
            "Enter the config path",
            default="hobot/locomotion/low_level/ppg_whole_body_conf.py",
        ).unsafe_ask()

        # Ask the user for overrides
        overrides = {}
        while True:
            key = questionary.text(
                "Enter override key (leave blank to finish)"
            ).unsafe_ask()
            if not key:
                break
            value = questionary.text("Enter override value").unsafe_ask()
            overrides[key] = value

        # TODO(breakds): Should not hard code here.
        agent_blacklist = questionary.checkbox(
            "Blacklist the following agents",
            choices=[
                "gail3",
                "samaritan",
                "lothric",
                "lorian",
                "octavian",
                "malenia",
            ],
        ).unsafe_ask()

        env = Environment()
        template = env.from_string(_JOB_TEMPLATE)
        json = template.render(
            project=project,
            group=group,
            name=name,
            notes=notes,
            branch=branch,
            config_path=config_path,
            overrides=overrides,
            agent_blacklist=agent_blacklist,
        )
        return JobRequest.parse_raw(json)
    except KeyboardInterrupt:
        return None
