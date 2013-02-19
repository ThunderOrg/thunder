<?php
   require_once("scripts/CARECloud.php");
   if (!$authorization->CheckLogin() || $authorization->GetRole() != "ADMIN") {
      $authorization->Redirect("index.php");
      exit;
   }
?>

<!DOCTYPE html>
<html>
<head>
<title>UA Care - Education Cloud</title>
<link rel="stylesheet" href="css/uacare.css"></link>
</head>
<body>
<div id="header"><a class="menuitem" href="help.html">Help</a><a class="menuitem" href="logout.php">Logout</a><p id="welcome">Welcome <?php echo $authorization->GetName(); ?></p></div>
<p><?php echo $comm->getSysInfo("PRIMARY_COMPUTE"); ?></p>
<p id="corner">Revision 2</p>
</body>
</html>
