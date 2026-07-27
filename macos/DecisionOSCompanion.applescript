-- APPLET_PICKER_ENTRY_BEGIN
on run arguments
	if (count of arguments) > 0 and item 1 of arguments is "pick" then
		try
			set selectedFolder to choose folder with prompt "Choose one local Git repository"
			return POSIX path of selectedFolder
		on error number -128
			return ""
		end try
	end if
-- APPLET_PICKER_ENTRY_END

	try
		set pythonBinary to __PYTHON_BINARY__
		set runtimeRoot to __RUNTIME_ROOT__
		set pickerPath to runtimeRoot & "/macos/DecisionOSCompanion.applescript"
		set launchCommand to "/usr/bin/env PYTHONPATH=" & quoted form of runtimeRoot & " DECISION_OS_COMPANION_PICKER_SCRIPT=" & quoted form of pickerPath & " " & quoted form of pythonBinary & " -m decision_os.companion"
		do shell script launchCommand
	on error errorMessage
		display dialog "Decision OS Companion could not start." & return & errorMessage buttons {"OK"} default button "OK" with icon stop
	end try
end run
