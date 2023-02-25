{ lib
, buildPythonPackage
, loguru
, libtmux
, fastapi
, prompt-toolkit
, uvicorn
, pydantic
, paramiko
, requests
, questionary
, jinja2
, rich
}:

buildPythonPackage {
  pname = "traintrack";
  version = "0.1.0";

  src = ../../../.;

  propagatedBuildInputs = [
    loguru
    libtmux
    fastapi
    prompt-toolkit
    uvicorn
    pydantic
    paramiko
    requests
    questionary
    jinja2
    rich
  ];

  doCheck = false;

  meta = with lib; {
    description = "Manages and schedules the training jobs on a cluster of machines";
    homepage = "https://github.com/breakds/traintrack";
    license = licenses.mit;
    maintainers = with maintainers; [ breakds ];
  };
}
