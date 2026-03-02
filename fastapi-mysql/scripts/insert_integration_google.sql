-- Insert user, workspace, and one integration record (GOOGLE) from given JSON
USE meta_poc;

-- 1. User (id=1) from integration.user
INSERT IGNORE INTO `user` (id, email, name, phone) VALUES
(1, 'dbiswa4u85@gmail.com', 'Biswa Poc', NULL);

-- 2. Workspace (id=1) for user_id=1
INSERT IGNORE INTO workspace (id, user_id, workspace_name) VALUES
(1, 1, 'My Workspace');

-- 3. Integration (GOOGLE)
INSERT INTO integration (
  user_id,
  workspace_id,
  ad_platform,
  status,
  email,
  ad_login_userinfo,
  ads_account,
  access_removed,
  last_authenticated,
  updated_at
) VALUES (
  1,
  1,
  'GOOGLE',
  1,
  'nyxadsolutions@gmail.com',
  '{"id":"102150492889045386344","name":"Nyx Ad solutions","email":"nyxadsolutions@gmail.com","picture":"https://lh3.googleusercontent.com/a/ACg8ocLDbyqTVnxKVl3e9L6ElmwxmrjU3bNx7hESE01sXoVLOCo3=s96-c","given_name":"Nyx","family_name":"Ad solutions","verified_email":true}',
  '[
    {"id":186,"account_id":"7581072325","account_name":"Luxury Watch Works"},
    {"id":189,"account_id":"2424589521","account_name":"SuccessTea"},
    {"id":190,"account_id":"5622277166","account_name":"Ikonic World"},
    {"id":192,"account_id":"6943451007","account_name":"Success Tea"}
  ]',
  0,
  '2026-02-12 08:59:54',
  '2026-02-16 21:00:14'
);
