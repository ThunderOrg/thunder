<?php
   include_once("scripts/test.php")
?>

<!DOCTYPE html>
<html>
<head>
<title>UA Care - Education Cloud</title>
<link rel="stylesheet" href="css/uacare.css"></link>
</head>
<body>
<div id="header"><a class="menuitem" href="help.html">Help</a></div>
<div id = "vcontainer">
	<p id="logo">UA CARE</p>
	<p class="sublogo">Education Cloud</p><br />
	<img id="sep" src="./images/line.png" />
	<form class="form-container">
		<label for="username">Username</label>
		<input class="form-field" type="text" name="username" required/><br />
		<label for="password">Password</label>
		<input class="form-field" type="password" name="password" required/><br />
		<div class="submit-container">
		<input class="submit-button" type="submit" value="Login" />
	</form>
</div>
<p id="corner">Revision 2</p>
</body>
</html>
