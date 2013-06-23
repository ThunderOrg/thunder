<?php
   require_once("scripts/thunder.php");
   if (!$authorization->CheckLogin()) {
      $authorization->Redirect("index.php");
      exit;
   }
?>

<!DOCTYPE html>
<html>
<head>
<title>Thunder - Education Cloud</title>
<link rel="stylesheet" href="css/thunder.css"></link>
</head>
<body>
<div id="header"><div id="rightHeader"><a class="menuitem" href="logout.php">Logout</a></div></div>
<div id="leftMenu">
   <a id="homeButton" href="<?php $authorization->GetSelfScript(); ?>">Home</a>
</div>
<div id="adminContent">
  <?php
     session_start();
     if (isset($_SESSION['mode'])) {
        if ($_SESSION['mode'] == "file") {
           if (isset($_SESSION['dat_file'])) {
              $file = $_SESSION['dat_file'];
              echo file_get_contents($file);
           }
        } else if ($_SESSION['mode'] == "data") {
           echo $_SESSION['data'];
        }
        unset($_SESSION['mode']);
        $_SESSION['mode'] = NULL;
        unset($_SESSION['dat_file']);
        $_SESSION['dat_file'] = NULL;
        unset($_SESSION['data']);
        $_SESSION['data'] = NULL;
     } else {
	echo "<p id=\"logo\">Thunder</p>";
     }
  ?>
</div>
<p id="corner"><?php echo $authorization->GetName(); ?></p>
</body>
</html>
