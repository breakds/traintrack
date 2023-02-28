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


def prompt_for_locomotion_job() -> JobRequest | None:
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
