import tecplot as tp
from funfluid.tecplot.utils.connect import new_layout_connect
from tecplot.constant import *


def plot1(data_v="", data_par=""):
    new_layout_connect()
    tp.macro.execute_command(f"""$!ReadDataSet  '\"{data_v}\" '
      ReadDataOption = New
      ResetStyle = No
      VarLoadMode = ByName
      AssignStrandIDs = Yes
      VarNameList = '\"V1\" \"V2\" \"V3\" \"V4\" \"V5\" \"V6\" \"V7\"'""")
    tp.macro.execute_command(f"""$!ReadDataSet  '\"{data_par}\" '
      ReadDataOption = Append
      ResetStyle = No
      VarLoadMode = ByName
      AssignStrandIDs = Yes
      VarNameList = '\"V1\";\"X\" \"V2\";\"Y\" \"V3\" \"V4\" \"V5\" \"V6\" \"V7\" \"T\"'""")
    tp.active_frame().plot().rgb_coloring.red_variable_index = 2
    tp.active_frame().plot().rgb_coloring.green_variable_index = 2
    tp.active_frame().plot().rgb_coloring.blue_variable_index = 2
    tp.active_frame().plot().contour(0).variable_index = 2
    tp.active_frame().plot().contour(1).variable_index = 3
    tp.active_frame().plot().contour(2).variable_index = 4
    tp.active_frame().plot().contour(3).variable_index = 5
    tp.active_frame().plot().contour(4).variable_index = 6
    tp.active_frame().plot().contour(5).variable_index = 7
    tp.active_frame().plot().contour(6).variable_index = 2
    tp.active_frame().plot().contour(7).variable_index = 2
    tp.active_frame().plot().show_contour = True
    tp.active_frame().plot().contour(0).variable_index = 3
    tp.active_frame().plot().contour(0).levels.reset_levels(
        [
            -1e-05,
            -8e-06,
            -6e-06,
            -4e-06,
            -2e-06,
            0,
            2e-06,
            4e-06,
            6e-06,
            8e-06,
            1e-05,
            1.2e-05,
            1.4e-05,
            1.6e-05,
            1.8e-05,
            2e-05,
        ]
    )
    tp.active_frame().plot().contour(1).variable_index = 7
    tp.active_frame().plot().contour(1).levels.reset_levels([0])
    tp.active_frame().plot().contour(1).colormap_name = "GrayScale"
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 5.53987005316
      Y = 5.25738334318
      ConsiderStyle = Yes""")
    tp.macro.execute_command("$!Pick Copy")
    tp.macro.execute_command("$!Pick Clear")
    tp.macro.execute_command("""$!AttachGeom 
      AnchorPos
        {
        X = 400.694497
        Y = 250
        }
      Color = Custom30
      FillColor = Black
      LineThickness = 0.4
      ArrowheadAttachment = AtEnd
      ArrowheadSize = 2
      RawData
    1
    2
    0 0 
    14.1102828979 0""")
    tp.active_frame().plot().view.zoom(
        xmin=216.255, xmax=615.295, ymin=78.7593, ymax=442.92
    )
    tp.active_frame().plot().view.zoom(
        xmin=292.456, xmax=491.976, ymin=163.522, ymax=345.602
    )
    tp.macro.execute_command("""$!Pick SetMouseMode
      MouseMode = Select""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 5.79503839338
      Y = 4.60883047844
      ConsiderStyle = Yes""")
    tp.active_frame().plot().fieldmaps(1).contour.flood_contour_group_index = 1
    tp.active_frame().plot().axes.x_axis.min = 300.313
    tp.active_frame().plot().axes.x_axis.max = 499.833
    tp.active_frame().plot().axes.y_axis.min = 161.322
    tp.active_frame().plot().axes.y_axis.max = 343.402
    tp.active_frame().plot(PlotType.Cartesian2D).vector.u_variable_index = 3
    tp.active_frame().plot(PlotType.Cartesian2D).vector.v_variable_index = 4
    tp.active_frame().plot().streamtraces.timing.reset_delta()
    tp.active_frame().plot().show_streamtraces = True
    tp.active_frame().plot().streamtraces.add(
        seed_point=[418.777, 222.196], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.color = Color.White
    tp.active_frame().plot().streamtraces.add(
        seed_point=[385.465, 201.455], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[412.492, 178.828], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[402.121, 290.078], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[409.978, 321.505], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[420.034, 285.05], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[445.804, 208.054], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[427.577, 274.05], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[411.235, 236.024], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[409.349, 262.423], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[364.723, 215.911], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[349.324, 275.936], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[321.355, 180.085], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[318.841, 315.219], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[399.921, 333.761], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[402.121, 165.943], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[470.631, 251.423], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().contour(0).levels.add([-3.64811e-07])
    tp.active_frame().plot().contour(0).levels.add([-2.38546e-07])
    tp.active_frame().plot().contour(0).levels.add([4.8665e-07])
    tp.active_frame().plot().contour(0).levels.add([2.66247e-07])
    tp.macro.execute_command("""$!Pick SetMouseMode
      MouseMode = Select""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 2.16952155936
      Y = 4.74704666273
      ConsiderStyle = Yes""")
    tp.active_frame().plot().axes.y_axis.show = False
    tp.active_frame().plot().axes.x_axis.show = False
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 9.3780271707
      Y = 2.00398700532
      ConsiderStyle = Yes""")
    tp.macro.execute_command("$!Pick Copy")
    tp.active_frame().plot().contour(1).legend.show = False
    tp.active_frame().plot().contour(0).legend.show = False
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 9.50561134082
      Y = 8.23434731246
      ConsiderStyle = Yes""")
    tp.macro.execute_command("""$!FrameControl ActivateByNumber
      Frame = 1""")
    tp.active_frame().plot().frame.transparent = True
    tp.active_frame().plot().frame.show_border = False
    tp.active_frame().plot().axes.y_axis.min = 161.636
    tp.active_frame().plot().axes.y_axis.max = 343.717
    # End Macro.


def plot2(data_v="", data_par=""):
    new_layout_connect()
    tp.macro.execute_command(f"""$!ReadDataSet  '\"{data_v}\" '
      ReadDataOption = New
      ResetStyle = No
      VarLoadMode = ByName
      AssignStrandIDs = Yes
      VarNameList = '\"x\" \"y\" \"u\" \"ux\" \"uy\" \"w\" \"p\"'""")
    tp.macro.execute_command(f"""$!ReadDataSet  '\"{data_par}\" '
      ReadDataOption = Append
      ResetStyle = No
      VarLoadMode = ByName
      AssignStrandIDs = Yes
      VarNameList = '\"x\" \"y\" \"u\" \"ux\" \"uy\" \"w\" \"p\" \"T\"'""")
    tp.active_frame().plot().contour(0).variable_index = 3
    tp.active_frame().plot().contour(0).variable_index = 2
    tp.active_frame().plot().contour(
        0
    ).colormap_filter.distribution = ColorMapDistribution.Continuous
    tp.active_frame().plot().contour(0).colormap_filter.continuous_min = -4
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 0.5
    tp.active_frame().plot().contour(0).colormap_filter.continuous_max = 0.8
    tp.active_frame().plot().rgb_coloring.red_variable_index = 2
    tp.active_frame().plot().rgb_coloring.green_variable_index = 2
    tp.active_frame().plot().rgb_coloring.blue_variable_index = 2
    tp.active_frame().plot().contour(1).variable_index = 3
    tp.active_frame().plot().contour(2).variable_index = 4
    tp.active_frame().plot().contour(3).variable_index = 6
    tp.active_frame().plot().contour(4).variable_index = 7
    tp.active_frame().plot().contour(5).variable_index = 2
    tp.active_frame().plot().contour(6).variable_index = 2
    tp.active_frame().plot().contour(7).variable_index = 2
    tp.active_frame().plot().show_contour = True
    tp.active_frame().plot().contour(1).variable_index = 7
    tp.active_frame().plot().contour(1).levels.reset_levels([0])
    tp.active_frame().plot().contour(1).colormap_name = "Raw User Defined"
    tp.active_frame().plot().contour(0).levels.reset_levels(
        [-4, -3.5, -3, -2.5, -2, -1.5, -1, -0.5, 0, 0.5]
    )
    tp.active_frame().plot().axes.x_axis.min = 11.0565
    tp.active_frame().plot().axes.x_axis.max = 809.136
    tp.active_frame().plot().axes.y_axis.min = -6.5424
    tp.active_frame().plot().axes.y_axis.max = 721.779
    tp.active_frame().plot().axes.y_axis.min = 13.5707
    tp.active_frame().plot().axes.y_axis.max = 741.892
    tp.active_frame().plot().view.zoom(
        xmin=204.942, xmax=603.982, ymin=69.9598, ymax=434.121
    )
    tp.active_frame().plot().view.zoom(
        xmin=301.256, xmax=500.776, ymin=167.293, ymax=349.374
    )
    tp.macro.execute_command("""$!Pick SetMouseMode
      MouseMode = Select""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 5.89072652097
      Y = 4.59819846426
      ConsiderStyle = Yes""")
    tp.macro.execute_command("$!Pick Copy")
    tp.macro.execute_command("$!Pick Clear")
    tp.macro.execute_command("""$!AttachGeom 
      AnchorPos
        {
        X = 400.669887
        Y = 250
        }
      Color = Red
      FillColor = Black
      LineThickness = 0.4
      ArrowheadAttachment = AtEnd
      ArrowheadSize = 2
      RawData
    1
    2
    0 0 
    14.1102828979 0""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 5.34849379799
      Y = 4.64072652097
      ConsiderStyle = Yes""")
    tp.active_frame().plot().fieldmaps(1).contour.flood_contour_group_index = 1
    tp.active_frame().plot().axes.x_axis.min = 300.941
    tp.active_frame().plot().axes.x_axis.max = 500.461
    tp.active_frame().plot().axes.y_axis.min = 166.979
    tp.active_frame().plot().axes.y_axis.max = 349.059
    tp.active_frame().plot(PlotType.Cartesian2D).vector.u_variable_index = 3
    tp.active_frame().plot(PlotType.Cartesian2D).vector.v_variable_index = 4
    tp.active_frame().plot().streamtraces.timing.reset_delta()
    tp.active_frame().plot().show_streamtraces = True
    tp.active_frame().plot().streamtraces.add(
        seed_point=[346.81, 250.795], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[349.01, 222.511], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[343.982, 239.481], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[357.495, 273.108], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[337.068, 266.194], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[436.062, 267.765], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[414.378, 308.62], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[436.69, 237.596], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[443.29, 208.369], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[414.692, 173.799], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[475.345, 183.227], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[356.867, 206.483], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[356.552, 287.878], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[445.176, 285.05], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[457.746, 252.68], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[399.293, 201.141], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.color = Color.White
    tp.active_frame().plot().streamtraces.line_thickness = 0.3
    tp.active_frame().plot().axes.x_axis.min = 300.627
    tp.active_frame().plot().axes.x_axis.max = 500.147
    tp.active_frame().plot().streamtraces.add(
        seed_point=[340.211, 307.991], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[462.46, 311.762], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[460.575, 190.141], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[350.267, 188.884], stream_type=Streamtrace.TwoDLine
    )
    tp.active_frame().plot().streamtraces.add(
        seed_point=[405.578, 185.742], stream_type=Streamtrace.TwoDLine
    )
    tp.macro.execute_command("""$!Pick SetMouseMode
      MouseMode = Select""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 2.16952155936
      Y = 2.96086828116
      ConsiderStyle = Yes""")
    tp.active_frame().plot().axes.y_axis.show = False
    tp.active_frame().plot().axes.x_axis.show = False
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 9.73951565269
      Y = 6.34184878913
      ConsiderStyle = Yes""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 9.29297105729
      Y = 2.30168340224
      ConsiderStyle = Yes""")
    tp.macro.execute_command("$!Pick Copy")
    tp.active_frame().plot().contour(1).legend.show = False
    tp.active_frame().plot().contour(0).legend.show = False
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 9.54813939752
      Y = 6.39500886001
      ConsiderStyle = Yes""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 9.03780271707
      Y = 4.24734199646
      ConsiderStyle = Yes""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 9.39929119905
      Y = 6.37374483166
      ConsiderStyle = Yes""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 9.39929119905
      Y = 6.29932073243
      ConsiderStyle = Yes""")
    tp.macro.execute_command("""$!Pick AddAtPosition
      X = 5.36975782634
      Y = 0.579297105729
      ConsiderStyle = Yes""")
    tp.active_frame().plot().axes.x_axis.min = 304.713
    tp.active_frame().plot().axes.x_axis.max = 504.233
    tp.active_frame().plot().axes.y_axis.min = 171.379
    tp.active_frame().plot().axes.y_axis.max = 353.459
    tp.active_frame().plot().axes.x_axis.min = 302.513
    tp.active_frame().plot().axes.x_axis.max = 502.033
    tp.active_frame().plot().axes.y_axis.min = 163.522
    tp.active_frame().plot().axes.y_axis.max = 345.602
    tp.active_frame().plot().axes.x_axis.min = 301.57
    tp.active_frame().plot().axes.x_axis.max = 501.09
    # End Macro.
