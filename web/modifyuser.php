<?php
   require_once("scripts/thunder.php");
   if (!$authorization->CheckLogin() || $authorization->GetRole() != "ADMIN") {
      $authorization->Redirect("index.php");
      exit;
   }
   $button = "";
   foreach ($_POST as $entry) {
      if (isset($entry)) {
         if ($entry == "Delete" || $entry == "Save") {
            $button = $entry;
         }
      }
   }
   $username = $_POST['Username'];
   $fname = $_POST['First_Name'];
   $lname = $_POST['Last_Name'];
   $role = $_POST['Role'];
   $pass = "";
   if ($_POST['Password'] != "") {
      $pass = hash("sha256", $_POST['Password']);
   }

   if ($button == "Save") {
      // Save info
      $authorization->UpdateUser($username, $fname, $lname, $role, $pass);
   } else if ($button == "Delete") {
      // Delete user
      $authorization->DeleteUser($username);
   }
   $authorization->Redirect("admin.php");
?>
