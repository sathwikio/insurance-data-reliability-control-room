/* Interpose getpwuid/getpwuid_r: the sandbox has no passwd entry for the
   current user, which crashes Hadoop's UnixLoginModule inside the JVM.
   We return a fake passwd struct instead. Uses __DATA,__interpose so dyld
   applies it even in two-level namespace binaries. */
#include <pwd.h>
#include <string.h>
#include <stddef.h>
#include <sys/types.h>

typedef struct interpose_s {
    void *replacement;
    void *original;
} interpose_t;
#define INTERPOSE(_repl, _orig)                                              \
    __attribute__((used)) static const interpose_t interpose_##_orig          \
    __attribute__((section("__DATA,__interpose"))) = {(void *)_repl, (void *)_orig};

static struct passwd *fake(uid_t uid) {
    static struct pwd_ptr {
        struct passwd p;
        char namebuf[64];
        char gecosbuf[64];
    } s;
    struct passwd *p = &s.p;
    strcpy(s.namebuf, "sathwik");
    strcpy(s.gecosbuf, "sathwik");
    p->pw_name = s.namebuf;
    p->pw_passwd = "*";
    p->pw_uid = uid;
    p->pw_gid = 20;
    p->pw_change = 0;
    p->pw_class = "";
    p->pw_gecos = s.gecosbuf;
    p->pw_dir = "/Users/sathwik";
    p->pw_shell = "/bin/zsh";
    p->pw_expire = 0;
    return p;
}

static struct passwd *my_getpwuid(uid_t uid) {
    return fake(uid);
}

static int my_getpwuid_r(uid_t uid, struct passwd *pwd, char *buffer, size_t buflen, struct passwd **result) {
    if (!pwd || !buffer || !result || buflen < 128) {
        if (result) *result = NULL;
        return -1;
    }
    *pwd = *fake(uid);
    pwd->pw_name = buffer;
    pwd->pw_gecos = buffer + 8;
    memcpy(buffer, "sathwik", 8);
    memcpy(buffer + 8, "sathwik", 8);
    *result = pwd;
    return 0;
}

INTERPOSE(my_getpwuid, getpwuid)
INTERPOSE(my_getpwuid_r, getpwuid_r)
