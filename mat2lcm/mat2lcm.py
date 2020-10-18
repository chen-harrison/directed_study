import lcm
import numpy as np
import scipy.io as sio
import time
from inekf import contact_t, groundtruth_t, imu_t, legcontrol_t

# NOTE: one potential source of confusion is that the loaded dictionary
# variables share similar names to the message types with "_t" endings: these
# hold the timestamps for each of the different sets of messages

# 4 CHANNELS:
#
# CHANNEL 1: 'ground_truth'
# int8_t  num_legs;
# double  mocap_timestamp;
# int8_t  contact[num_legs];
#
# CHANNEL 2: 'contact_data'
# int8_t  num_joints;
# double  lcm_timestamp;
# double  tau_feed_back[num_joints];
# double  tau_feed_forward[num_joints];
#
# CHANNEL 3: 'leg_control_data'
# int8_t  num_joints;
# double  lcm_timestamp;
# double  q[num_joints];
# double  p[num_joints];
# double  qd[num_joints];
# double  v[num_joints];
# double  tau_est[num_joints];
#
# CHANNEL 4: 'microstrain'
# double  lcm_timestamp;
# double  acc[3];
# double  omega[3];

def main():
    PATH = '/home/harrison/Documents/CURLY/mat2lcm/sync_data.mat'
    sync_data = sio.loadmat(PATH)

    log = lcm.EventLog('sync_data.log', mode='w', overwrite=True)
    utime = int(time.time() * 10**6)
    num_legs = 4
    num_joints = 3 * num_legs

    # pull variables from mat file
    m_t = sync_data['mocap_t'].flatten().tolist()
    labels = sync_data['contact_labels'].tolist()

    c_t = sync_data['contact_t'].flatten().tolist()
    tau_fb = sync_data['lcm_tau_fb'].tolist()
    tau_ff = sync_data['lcm_tau_ff'].tolist()

    l_t = sync_data['legcontrol_t'].flatten().tolist()
    q = sync_data['lcm_q'].tolist()
    p = sync_data['lcm_p'].tolist()
    qd = sync_data['lcm_qd'].tolist()
    v = sync_data['lcm_v'].tolist()
    tau_est = sync_data['lcm_tau_est'].tolist()

    i_t = sync_data['imu_t'].flatten().tolist()
    acc = sync_data['lcm_acc'].tolist()
    gyro = sync_data['lcm_gyro'].tolist()

    # combine all timestamps, remove duplicates, and sort
    all_t = list(set(m_t + c_t + l_t + i_t))
    all_t.sort()
    
    # indices to move iterate through different messages
    m, c, l, i = 0, 0, 0, 0
    complete_flag = [False] * 4

    for current_timestamp in all_t:
        if not complete_flag[0] and m_t[m] == current_timestamp:
            msg = groundtruth_t()
            msg.num_legs = num_legs
            msg.mocap_timestamp = m_t[m]
            msg.contact = labels[m]

            log.write_event(utime + int(10**6 * m_t[m]), 'ground_truth', msg.encode())
            m += 1
            if m == len(m_t):
                complete_flag[0] = True
                print('ground_truth complete')
        
        if not complete_flag[1] and c_t[c] == current_timestamp:
            msg = contact_t()
            msg.num_joints = num_joints
            msg.lcm_timestamp = c_t[c]
            msg.tau_feed_back = tau_fb[c]
            msg.tau_feed_forward = tau_ff[c]

            log.write_event(utime + int(10**6 * c_t[c]), 'contact_data', msg.encode())
            c += 1
            if c == len(c_t):
                complete_flag[1] = True
                print('contact_data complete')
        
        if not complete_flag[2] and l_t[l] == current_timestamp:
            msg = legcontrol_t()
            msg.num_joints = num_joints
            msg.lcm_timestamp = l_t[l]
            msg.q = q[l]
            msg.p = p[l]
            msg.qd = qd[l]
            msg.v = v[l]
            msg.tau_est = tau_est[l]

            log.write_event(utime + int(10**6 * l_t[l]), 'leg_control_data', msg.encode())
            l += 1
            if l == len(l_t):
                complete_flag[2] = True
                print('leg_control_data complete')
        
        if not complete_flag[3] and i_t[i] == current_timestamp:
            msg = imu_t()
            msg.lcm_timestamp = i_t[i]
            msg.acc = acc[i]
            msg.omega = gyro[i]

            log.write_event(utime + int(10**6 * i_t[i]), 'microstrain', msg.encode())
            i += 1
            if i == len(i_t):
                complete_flag[3] = True
                print('microstrain complete')
    
    print('\nDONE!')

if __name__ == '__main__':
    main()