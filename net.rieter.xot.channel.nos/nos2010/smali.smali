.class public Lnl/uitzendinggemist/b/v;
.super Ljava/lang/Object;
.source "SourceFile"


# static fields
.field public static final a:Ljava/lang/String;

.field private static final b:[C

.field private static final c:[C

.field private static final d:[C

.field private static final e:[C


# direct methods
.method static constructor <clinit>()V
    .locals 3

    const/4 v2, 0x7

    const/4 v1, 0x5

    const-class v0, Lnl/uitzendinggemist/b/v;

    invoke-virtual {v0}, Ljava/lang/Class;->getSimpleName()Ljava/lang/String;

    move-result-object v0

    sput-object v0, Lnl/uitzendinggemist/b/v;->a:Ljava/lang/String;

    new-array v0, v1, [C

    fill-array-data v0, :array_0

    sput-object v0, Lnl/uitzendinggemist/b/v;->b:[C

    new-array v0, v2, [C

    fill-array-data v0, :array_1

    sput-object v0, Lnl/uitzendinggemist/b/v;->c:[C

    new-array v0, v1, [C

    fill-array-data v0, :array_2

    sput-object v0, Lnl/uitzendinggemist/b/v;->d:[C

    new-array v0, v2, [C

    fill-array-data v0, :array_3

    sput-object v0, Lnl/uitzendinggemist/b/v;->e:[C

    return-void

    nop

    :array_0
    .array-data 0x2
        0x35t 0x0t
        0x24t 0x0t
        0x1t 0x0t
        0x40t 0x0t
        0x73t 0x0t
    .end array-data

    nop

    :array_1
    .array-data 0x2
        0x62t 0x0t
        0x77t 0x0t
        0x62t 0x0t
        0x6ct 0x0t
        0x61t 0x0t
        0x62t 0x0t
        0x73t 0x0t
    .end array-data

    nop

    :array_2
    .array-data 0x2
        0x2et 0x0t
        0x2et 0x0t
        0x2at 0x0t
        0x4ct 0x0t
        0x6at 0x0t
    .end array-data

    nop

    :array_3
    .array-data 0x2
        0x69t 0x0t
        0x40t 0x0t
        0x68t 0x0t
        0x3et 0x0t
        0x49t 0x0t
        0x9t 0x0t
        0xa7t 0xfft
    .end array-data
.end method

.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static a(JLjava/lang/String;I)Ljava/lang/String;
    .locals 9

    sget-object v0, Lnl/uitzendinggemist/b/v;->d:[C

    array-length v0, v0

    new-array v4, v0, [C

    const/4 v0, 0x1

    if-ne p3, v0, :cond_0

    const-string v0, "h264_sb"

    :goto_0
    const/4 v3, 0x0

    const/16 v2, 0xb

    const/4 v1, 0x7

    :goto_1
    array-length v5, v4

    if-lt v3, v5, :cond_2

    const-string v1, "%08x"

    const/4 v2, 0x1

    new-array v2, v2, [Ljava/lang/Object;

    const/4 v3, 0x0

    invoke-static {p0, p1}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;

    move-result-object v5

    aput-object v5, v2, v3

    invoke-static {v1, v2}, Ljava/lang/String;->format(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v5

    sget-object v1, Lnl/uitzendinggemist/b/v;->e:[C

    array-length v1, v1

    new-array v6, v1, [C

    const/4 v1, 0x0

    const/16 v3, 0x32

    const/4 v2, -0x3

    :goto_2
    array-length v7, v6

    if-lt v1, v7, :cond_3

    const/4 v1, 0x0

    :goto_3
    array-length v2, v4

    if-lt v1, v2, :cond_4

    const/4 v1, 0x0

    :goto_4
    array-length v2, v6

    if-lt v1, v2, :cond_5

    array-length v1, v6

    add-int/lit8 v1, v1, -0x1

    array-length v2, v4

    add-int/lit8 v3, v2, -0x1

    aget-char v2, v6, v1

    xor-int/lit8 v2, v2, -0x3

    int-to-char v2, v2

    aput-char v2, v6, v1

    add-int/lit8 v2, v1, -0x1

    const/4 v1, -0x6

    :goto_5
    if-gez v2, :cond_6

    aget-char v1, v4, v3

    const/4 v2, 0x0

    aget-char v2, v6, v2

    add-int/lit8 v2, v2, 0x8

    xor-int/2addr v1, v2

    int-to-char v1, v1

    aput-char v1, v4, v3

    add-int/lit8 v2, v3, -0x1

    const/4 v1, 0x4

    :goto_6
    if-gez v2, :cond_7

    const-string v1, "%5$s%7$s%1$s%2$s%3$s%4$s%6$s"

    const/4 v2, 0x7

    new-array v2, v2, [Ljava/lang/Object;

    const/4 v3, 0x0

    const-string v7, "video"

    aput-object v7, v2, v3

    const/4 v3, 0x1

    const-string v7, "icougmobiel"

    aput-object v7, v2, v3

    const/4 v3, 0x2

    aput-object v0, v2, v3

    const/4 v3, 0x3

    aput-object p2, v2, v3

    const/4 v3, 0x4

    new-instance v7, Ljava/lang/String;

    invoke-direct {v7, v4}, Ljava/lang/String;-><init>([C)V

    aput-object v7, v2, v3

    const/4 v3, 0x5

    aput-object v5, v2, v3

    const/4 v3, 0x6

    new-instance v4, Ljava/lang/String;

    invoke-direct {v4, v6}, Ljava/lang/String;-><init>([C)V

    aput-object v4, v2, v3

    invoke-static {v1, v2}, Ljava/lang/String;->format(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v1

    invoke-static {v1}, Lnl/uitzendinggemist/b/aa;->b(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    const-string v2, "http://%s/%s/%s/%s/%s/%s/%s?type=http"

    const/4 v3, 0x7

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    const-string v6, "odi.omroep.nl"

    aput-object v6, v3, v4

    const/4 v4, 0x1

    const-string v6, "video"

    aput-object v6, v3, v4

    const/4 v4, 0x2

    const-string v6, "icougmobiel"

    aput-object v6, v3, v4

    const/4 v4, 0x3

    aput-object v0, v3, v4

    const/4 v0, 0x4

    aput-object v1, v3, v0

    const/4 v0, 0x5

    aput-object v5, v3, v0

    const/4 v0, 0x6

    aput-object p2, v3, v0

    invoke-static {v2, v3}, Ljava/lang/String;->format(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v0

    return-object v0

    :cond_0
    const/4 v0, 0x2

    if-ne p3, v0, :cond_1

    const-string v0, "h264_std"

    goto/16 :goto_0

    :cond_1
    const-string v0, "h264_sb"

    goto/16 :goto_0

    :cond_2
    sget-object v5, Lnl/uitzendinggemist/b/v;->d:[C

    aget-char v5, v5, v3

    xor-int/2addr v5, v2

    neg-int v6, v1

    add-int/2addr v5, v6

    int-to-char v5, v5

    aput-char v5, v4, v3

    add-int/lit8 v3, v3, 0x1

    add-int/lit8 v2, v2, 0x3

    add-int/lit8 v1, v1, -0x2

    goto/16 :goto_1

    :cond_3
    sget-object v7, Lnl/uitzendinggemist/b/v;->e:[C

    aget-char v7, v7, v1

    xor-int/2addr v7, v3

    neg-int v8, v2

    add-int/2addr v7, v8

    int-to-char v7, v7

    aput-char v7, v6, v1

    add-int/lit8 v1, v1, 0x1

    add-int/lit8 v3, v3, 0x5

    add-int/lit8 v2, v2, 0x3

    goto/16 :goto_2

    :cond_4
    aget-char v2, v4, v1

    sget-object v3, Lnl/uitzendinggemist/b/v;->b:[C

    aget-char v3, v3, v1

    xor-int/2addr v2, v3

    int-to-char v2, v2

    aput-char v2, v4, v1

    add-int/lit8 v1, v1, 0x1

    goto/16 :goto_3

    :cond_5
    aget-char v2, v6, v1

    sget-object v3, Lnl/uitzendinggemist/b/v;->c:[C

    aget-char v3, v3, v1

    xor-int/2addr v2, v3

    int-to-char v2, v2

    aput-char v2, v6, v1

    add-int/lit8 v1, v1, 0x1

    goto/16 :goto_4

    :cond_6
    aget-char v7, v6, v2

    add-int/lit8 v8, v2, 0x1

    aget-char v8, v6, v8

    add-int/2addr v8, v1

    xor-int/2addr v7, v8

    int-to-char v7, v7

    aput-char v7, v6, v2

    add-int/lit8 v2, v2, -0x1

    add-int/lit8 v1, v1, 0x2

    goto/16 :goto_5

    :cond_7
    aget-char v3, v4, v2

    add-int/lit8 v7, v2, 0x1

    aget-char v7, v4, v7

    add-int/2addr v7, v1

    xor-int/2addr v3, v7

    int-to-char v3, v3

    aput-char v3, v4, v2

    add-int/lit8 v2, v2, -0x1

    add-int/lit8 v1, v1, -0x4

    goto/16 :goto_6
.end method