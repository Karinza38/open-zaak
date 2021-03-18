@echo off

for /F "tokens=1" %%i in ('git rev-parse --show-toplevel') do set toplevel=%%i

cd %toplevel%

REM Base deps
pip-compile^
    requirements/base.in

REM Dependencies for testing
pip-compile^
    --output-file requirements/ci.txt^
    requirements/base.txt^
    requirements/test-tools.in

REM Dev depedencies - exact same set as CI + some extra tooling
pip-compile^
    --output-file requirements/dev.txt^
    requirements/ci.txt^
    requirements/dev.in
