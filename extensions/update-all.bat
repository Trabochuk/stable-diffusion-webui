for /d %%i in (*) do @if exist "%%i\.git" (echo Pulling updates for %%i... & git -C "%%i" pull)