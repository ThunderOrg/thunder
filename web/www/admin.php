<?php
   require_once("scripts/thunder.php");
   if (!$authorization->CheckLogin() || $authorization->GetRole() != "ADMIN") {
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
   <div>
   <a id="homeButton" href="<?php $authorization->GetSelfScript(); ?>">Home</a>
   <details open="open">
      <summary>Manage</summary>
      <div style="margin-left: 10px;">  
      <details open="open">
         <summary>Clusters</summary>
         <ul>
	      <?php
		 $cluster = $comm->getClusterList();
		 if (count($cluster)==0) {
		    echo "<li>No clusters found</li>";
		 } else {
		    for ($i=0;$i<count($cluster);$i = $i +1) {
		       echo "<li><a href=\"getClusterData.php?cname=".$cluster[$i]."\">".ucwords(strtolower(str_replace("_"," ",$cluster[$i])))."</a></li>";
		    }
		 }
	      ?>
         </ul>
      </details>
      <details open="open">
         <summary>Users</summary>
          <ul>
	      <?php
		 $users = $authorization->getUserList();
		 if (count($users)==0) {
		    echo "<li>No users found</li>";
		 } else {
		    for ($i=0;$i<count($users);$i++) {
		       echo "<li><a href=\"getUserData.php?uname=".$users[$i]."\">".$authorization->getFullName($users[$i])."</a></li>";
		    }
		 }
	      ?>
              <li><a href="genAddUser.php">Add New User</a></li>
         </ul>
      </details>
      <details open="open">
         <summary>Images</summary>
      </details>
      </div>
   </details> <br />
   <details open="open">
      <summary>Tools</summary>
   </details>
   </div>
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
	echo "<p class=\"sublogo\">Management Console</p><br />";
     }
  ?>
</div>
<p id="corner"><?php echo $authorization->GetName(); ?></p>
</body>
</html>
