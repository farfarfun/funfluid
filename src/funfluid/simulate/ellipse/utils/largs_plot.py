import matplotlib.pyplot as plt


def largs_plot_speed(df):
    plt.figure(figsize=(6, 6))
    ax = plt.axes()

    def plot_larg(row):
        ax.arrow(
            row["lx"],
            row["ly"],
            row["ux"],
            row["uy"],
            color="b",
            linewidth=0.5,
            head_width=0.5,
            head_length=0.5,
        )

    plt.plot(df["lx"], df["ly"], "-o")
    df.apply(plot_larg, axis=1)
    plt.xlim(
        df["lx"].min() - df["ux"].abs().max() - 5,
        df["lx"].max() + df["ux"].abs().max() + 5,
    )
    plt.ylim(
        df["ly"].min() - df["uy"].abs().max() - 5,
        df["ly"].max() + df["uy"].abs().max() + 5,
    )

    plt.grid(b=True, which="major")
