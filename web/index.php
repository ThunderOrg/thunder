<?php
   require_once("scripts/CARECloud.php");
   if (isset($_POST['submitted'])) {
      if ($authorization->Login()) {
         if ($authorization->GetRole() == 'ADMIN') {
            $authorization->Redirect("admin.php");
         } else if ($authorization->GetRole() == "STUDENT") {
            $authorization->Redirect("student.php");
         } else if ($authorization->GetRole() == "INSTRUCTOR") {
            $authorization->Redirect("instructor.php");
         }
      }
   } else if ($authorization->CheckLogin()) {
      if ($authorization->GetRole() == 'ADMIN') {
         $authorization->Redirect("admin.php");
      } else if ($authorization->GetRole() == "STUDENT") {
         $authorization->Redirect("student.php");
      } else if ($authorization->GetRole() == "INSTRUCTOR") {
         $authorization->Redirect("instructor.php");
      }
   }
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
	<form class="form-container" action="<?php echo $authorization->GetSelfScript(); ?>" method="post" accept-charset="UTF-8">
                <input type='hidden' name='submitted' id='submitted' value='1' />
		<label for="username">Username</label>
		<input class="form-field" type="text" name="username" required/><br />
		<label for="password">Password</label>
		<input class="form-field" type="password" name="password" required/><br />
		<div class="submit-container">
		<input class="submit-button" type="submit" value="Login" />
	</form>
        <?php echo "<p align=\"left\">".$authorization->GetErrorMessage()."</p>"; $authorization->ClearError()?>
</div>
<p id="corner">Revision 2</p>
</body>
</html>
