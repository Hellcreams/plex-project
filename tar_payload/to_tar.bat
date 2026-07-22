for /d %%D in (*) do (
	tar -cvf "%%D.tar" "%%D"
)
