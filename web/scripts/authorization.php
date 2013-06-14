<?php
class Authorization {
   var $username;
   var $passhash;
   var $connection;
   var $db;
   var $pwd;
   var $table;
   var $site_name;
   var $error_message;
   var $role;

   function Authorization() {
      $this->site_name = "Thunder Cloud";
   }

   function InitDB($host, $uname, $pwd, $db, $table) {
      $this->db_host = $host;
      $this->username = $uname;
      $this->pwd = $pwd;
      $this->db = $db;
      $this->table = $table;
   }

   function DBLogin() {
      $this->connection = mysql_connect($this->db_host, $this->username, $this->pwd);
      if (!$this->connection) {
         $this->HandleDBError("Could not connect to database!");
         return false;
      }
      if (!mysql_select_db($this->db, $this->connection)) {
         $this->HandleDBError("Could not select database!");
         return false;
      }
      if (!mysql_query("SET NAMES 'UTF8'", $this->connection)) {
         $this->HandleDBError("Could not set encoding to UTF8");
         return false;
      }
      return true;
   }

   function Login() {
      if (empty($_POST['username'])) {
         $this->HandleError("Username is empty!");
         return false;
      }
      if (empty($_POST['password'])) {
         $this->HandleError("Password is empty!");
         return false;
      }
      $username = trim($_POST['username']);
      $passhash = hash("sha256", trim($_POST['password']));
      if (!$this->CheckLoginInDB($username, $passhash)) {
         return false;
      }

      if (!isset($_SESSION)) {
         session_start();
      }

      $_SESSION['username'] = $username;
      $_SESSION['uuid'] = uniqid();
     
      return true;
   }

   function GetLoginSessionVar() {
      if (!isset($_SESSION)) {
         session_start();
      }
      if (isset($_SESSION['uuid'])) {
         $ret = $_SESSION['uuid'];
      } else {
         $ret = false;
      }
      return $ret;
   }

   function getUserList() {
      if (!$this->DBLogin()) {
         $this->HandleError("Database login failed!");
         return array();
      }
      $sql = "select username from user;";
      $res = mysql_query($sql, $this->connection);
      if (!$res || mysql_num_rows($res) <= 0) {
         $this->HandleError("The username or password are incorrect");
         return array();
      } else {
         $vals = mysql_fetch_array($res);
         return $vals;
      }
   }
 
   function getFullName($username) {
      if (!$this->DBLogin()) {
         $this->HandleError("Database login failed!");
         return false;
      }
      $sql = "select fname, lname from user where username='$username'";
      $res = mysql_query($sql, $this->connection);
      if (!$res || mysql_num_rows($res) <= 0) {
         $this->HandleError("The username or password are incorrect");
         return false;
      } else {
         $vals = mysql_fetch_assoc($res);
         return $vals['fname'] . ' ' . $vals['lname'];
      }
 
   }

   function Redirect($url) {
      header("Location: $url");
      exit;
   }
   
   function Logout() {
      if (!isset($_SESSION)) {
         session_start();
      }
      $_SESSION['uuid']=NULL;
      unset($_SESSION['uuid']);
      $_SESSION['username']=NULL;
      unset($_SESSION['username']);
      $_SESSION['role']=NULL;
      unset($_SESSION['role']);
      $_SESSION['name']=NULL;
      unset($_SESSION['name']);
      header("Location: index.php");
   }

   function UpdateUser($user, $fname, $lname, $role, $pass) {
      if (!$this->DBLogin()) {
         $this->HandleError("Database login failed!");
         return false;
      }
      $sql = "";
      if ($pass == "") {
         $sql = "update user set fname='$fname', lname='$lname', role='$role' where username='$user'";
      } else {
         $sql = "update user set fname='$fname', lname='$lname', role='$role' password='$pass' where username='$user'";
      }
      mysql_query($sql, $this->connection);
   }
   
   function DeleteUser($user) {
      if (!$this->DBLogin()) {
         $this->HandleError("Database login failed!");
         return false;
      }
      $sql = "delete from user where username='$user'";
      mysql_query($sql, $this->connection);
   }

   function CheckLoginInDB($username, $passhash) {
      if (!isset($_SESSION)) {
         session_start();
      }
      if (!$this->DBLogin()) {
         $this->HandleError("Database login failed!");
         return false;
      }
      $username = $this->SanitizeForSQL($username);
      $sql = "select fname, lname, role from user where username='$username' and password='$passhash'";

      $res = mysql_query($sql, $this->connection);

      if (!$res || mysql_num_rows($res) <= 0) {
         $this->HandleError("The username or password are incorrect");
         return false;
      } else {
         $vals = mysql_fetch_assoc($res);
         $_SESSION['role'] = $vals['role'];
         $_SESSION['name'] = $vals['fname'].' '.$vals['lname'];
      }
      return true;
   }

   function CheckLogin() {
      if (!isset($_SESSION)) {
         session_start();
      }
      if (empty($_SESSION['uuid'])) {
         return false;
      }
      return true;
   }

   function GetRole() {
      if (isset($_SESSION['role'])) {
         return $_SESSION['role'];
      } else {
         return -1;
      }
   }

   function GetName() {
      if (!isset($_SESSION)) {
         session_start();
      }
      if (isset($_SESSION['name'])) {
         return $_SESSION['name'];
      } else {
         return "unknown";
      }
 
   }

   function SanitizeForSQL($str) {
      if (function_exists("mysql_real_escape_string")) {
         $ret = mysql_real_escape_string($str);
      } else {
         $ret = addslashes($str);
      }
      return $ret;
   }

   function Sanitize($str, $remove_nl=true) {
      $str = $this->StripSlashes($str);
      
      if ($remove_nl) {
         $injections = array('/(\n+)/i', '/(\r+)/i', '/(\t+)/i', '/(%0A+)/i', '/(%0D+)/i', '/(%08+)/i', '/(%09+)/i');
         $str = preg_replace($injections,'',$str);
      }
      return $str;
   }

   function StripSlashes($str) {
      if (get_magic_quotes_gpc()) {
         $str = stripslashes($str);
      }
      return $str;
   }

   function SaveUser($user) {
      if (!$this->DBLogin()) {
         $this->HandleError("Database login failed!");
         return false;
      }
      session_start();
      $date = new DateTime();
      if (!file_exists('data/' . $_SESSION['uuid'] . '/')) {
         mkdir('data/' . $_SESSION['uuid'] . '/', 0755, true);
      }
      $file = "data/" . $_SESSION['uuid'] . "/" . $user . $date->getTimeStamp() . ".dat";
      $contents = "";

      $sql = "select * from user where username='$user'";
      $res = mysql_query($sql, $this->connection);

      $vals = mysql_fetch_assoc($res);
      $contents .= "readonly:Username:" . $vals['username'] . ";text:First_Name:" . $vals['fname'] . ";text:Last_Name:" . $vals['lname'] . ";text:Role:" . $vals['role'] . ";password:Password:";
      file_put_contents($file, $this->GenerateForm($contents));
      return $file;
   }

   function GenerateForm($text) {
      $entries = explode(';', $text);
      $data = "<div class=\"nodeinfo\"><form action=\"modifyuser.php\" method=\"POST\"><table>";
      for ($i=0;$i<count($entries);$i++) {
         $entry = explode(':',$entries[$i]);
         $type = $entry[0];
         $name = $entry[1];
         $label = str_replace('_',' ',$entry[1]);
         $value = $entry[2];
         if ($type == "readonly") {
            $data .= "<tr><td>$label</td><td><strong>$value</strong></td></tr><input type=\"hidden\" name=\"$name\" value=\"$value\">";
         } else {
            $data .= "<tr><td><label for=\"$name\">$label</label></td><td><input type=\"$type\" name=\"$name\" value=\"$value\"><br /></td></tr>";
         }
      }
      $data .= "</table><input class=\"floatright\" type=\"submit\" name=\"delete\" value=\"Delete\"><input class=\"floatright\" type=\"submit\" name=\"save\" value=\"Save\"><br /></form></div>";
      return $data;
   }

   function GetSelfScript() {
      return htmlentities($_SERVER['PHP_SELF']);
   }

   function GetErrorMessage() {
      if (empty($this->error_message)) {
         return '';
      }
      $errmsg = nl2br(htmlentities($this->error_message));
      return $errmsg;
   }

   function ClearError() {
      $this->error_message = '';
   }  
 
   function HandleError($msg) {
      // To do: Log error
      $this->error_message = $msg."\r\n";
   }

   function HandleDBError($msg) {
      // To do: Log Error
      $this->HandleError($msg);
   }
}
?>
