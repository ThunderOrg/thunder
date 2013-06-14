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
<div id="header"><div id="rightHeader"><a class="menuitem" href="logout.php"><?php echo $authorization->GetName(); ?></a></div></div>
<div id="leftMenu">
   <div>
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
		 if (count($users)==1) {
		    echo "<li>No users found</li>";
		 } else {
		    for ($i=0;$i<count($users)-1;$i = $i +1) {
		       echo "<li><a href=\"getUserData.php?uname=".$users[$i]."\">".$authorization->getFullName($users[$i])."</a></li>";
		    }
		 }
	      ?>
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
     if (isset($_SESSION['dat_file'])) {
        $file = $_SESSION['dat_file'];
        echo file_get_contents($file);
     }
  ?>
</div>
<p id="corner">Revision 2</p>
</body>
</html>
